import boto3
from boto3.dynamodb.conditions import Key
from chalice import Chalice, BadRequestError

from dateutil.parser import parse
from decimal import Decimal
import logging
import random

app = Chalice(app_name='mockledger-backend')
dynamodb = boto3.resource('dynamodb')
ledgers = dynamodb.Table('ledgers')
balances = dynamodb.Table('ledger_balances')
charges = dynamodb.Table('ledger_charges')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app.debug = True


@app.route('/ledgers/{customer_id}', methods=['POST'], cors=True)
def create_ledger(customer_id):
    # Random number - this obviously is not for real usage!
    account_id = str(random.randint(1, 999999999))
    # insert into DynamoDB
    ledgers.put_item(
        Item={
            'customer_id': customer_id,
            'account_id': account_id
            }
    )
    return {"account_id": account_id}


@app.route('/balances/{account_id}', methods=['GET'], cors=True)
def get_monthly_balances(account_id):
    params = app.current_request.query_params
    month = params.get('month')
    if not month:
        raise BadRequestError("Missing month query param")
    # This is lame - do it properly
    start_date = month + '-01'
    end_date = month + '-31'
    response = balances.query(
        KeyConditionExpression=Key('account_id').eq(account_id) & Key('ledger_date').between(start_date, end_date)
    )
    return response


@app.route('/balances/{account_id}/{ledger_date}', methods=['POST', 'GET'], cors=True)
def proccess_balances(account_id, ledger_date):
    # Get quantity from payload
    request = app.current_request
    if request.method == 'GET':
        balance_quantity = get_balance(account_id=account_id, ledger_date=ledger_date)
        return balance_quantity
    else:
        json_body = request.json_body
        if not json_body:
            raise BadRequestError("Missing balance quantity")
        balance_quantity = Decimal(json_body.get('balance_quantity'))
        # TODO - some validation on the date
        # ledger_date = parse(ledger_date).strftime("%Y-%m-%d")
        insert_balance(account_id=account_id, ledger_date=ledger_date, balance_quantity=balance_quantity)
        return {"balance_quantity": balance_quantity}


def insert_balance(account_id, ledger_date, balance_quantity):
    # insert into DynamoDB
    balances.put_item(
        Item={
            'account_id': account_id,
            'ledger_date': ledger_date,
            'balance_quantity': balance_quantity
            }
    )

def insert_charge(account_id, ledger_date, charge_type, charge_value):
    # insert into DynamoDB
    charges.put_item(
        Item={
            'account_id': account_id,
            'ledger_date': ledger_date,
            'charge_type': charge_type,
            'charge_value': charge_value
            }
    )

def get_balance(account_id, ledger_date):
    balance = balances.get_item(
        Key={
            'account_id': account_id,
            'ledger_date': ledger_date
            }
        )
    logger.info("Retrieved balance: %s for account_id: %s on date: %s", balance, account_id, ledger_date)
    balance_quantity = Decimal(balance['Item']['balance_quantity'])
    return balance_quantity


# CALCULATE EOD
@app.route('/eod/{account_id}/{ledger_date}', methods=['POST'], cors=True)
def post_eod(account_id, ledger_date):
    balance = get_balance(account_id=account_id, ledger_date=ledger_date) 
    crediting_rate = Decimal('0.01')
    crediting_amount = -1 * balance * crediting_rate
    logger.info("Crediting Amount: %s", crediting_amount)
    insert_charge(account_id=account_id, ledger_date=ledger_date, charge_type='credit', charge_value=crediting_amount)
    return crediting_amount

# Process EOD
@app.route('/eom/{account_id}/{ledger_month}', methods=['GET', 'POST'], cors=True)
def process_eom(account_id, ledger_month):
    logger.info("Processing EOD for account_id: %s for month: %s", account_id, ledger_month)
    # Get all charges for month
    # This is lame - do it properly
    start_date = ledger_month + '-01'
    end_date = ledger_month + '-31'
    response = charges.query(
        KeyConditionExpression=Key('account_id').eq(account_id) & Key('ledger_date').between(start_date, end_date)
    )
    # If it's a POST, also write the result back
    if app.current_request.method == 'POST':
        pass
    return response
    # Sum up charges
    # Move charge between ledgers
