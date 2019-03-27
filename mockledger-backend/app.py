import boto3
from boto3.dynamodb.conditions import Key
from chalice import Chalice, BadRequestError
import requests

import calendar
from datetime import date, datetime
from dateutil.parser import parse
from decimal import Decimal, ROUND_HALF_UP
import logging
import pytz
import random

app = Chalice(app_name='mockledger-backend')
dynamodb = boto3.resource('dynamodb')
ledgers = dynamodb.Table('ledgers')
balances = dynamodb.Table('ledger_balances')
charges = dynamodb.Table('ledger_charges')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
app.debug = True
main_charge_ledger = '5c9b118f-bb01-44e7-a2ad-a35fd691a9fc'
# For Liam
prototype_customer_id = '1'



@app.route('/ledgers/{customer_id}', methods=['POST'], cors=True)
def create_ledger(customer_id):
    # Random number - this obviously is not for real usage!
    account_id = str(random.randint(1, 999999999))
    
    json_body = app.current_request.json_body
    if not json_body:
        raise BadRequestError("Missing body")
    main_ledger = json_body.get('main_ledger')
    charge_ledger = json_body.get('charge_ledger')
    # insert into DynamoDB
    ledgers.put_item(
        Item={
            'customer_id': customer_id,
            'account_id': account_id,
            'main_ledger': main_ledger,
            'charge_ledger': charge_ledger
            }
    )
    return {"account_id": account_id}


@app.route('/balances/{account_id}', methods=['GET'], cors=True)
def get_monthly_balances(account_id):
    params = app.current_request.query_params
    year_month = params.get('month')
    if not year_month:
        raise BadRequestError("Missing month query param")
    # This is lame - do it properly
    start_date = year_month + '-01'
    year, month = year_month.split('-')
    end_date = year_month + '-' + str(calendar.monthrange(int(year), int(month))[1])
    response = balances.query(
        KeyConditionExpression=Key('account_id').eq(account_id) & Key('ledger_date').between(start_date, end_date)
    )
    return response


@app.route('/balances/{account_id}/{ledger_date}', methods=['POST', 'GET'], cors=True)
def proccess_balances(account_id, ledger_date):
    logger.info("Processing Balance")
    # Get quantity from payload
    request = app.current_request
    if request.method == 'GET':
        logger.info("Getting balance for date: %s", ledger_date)
        balance_quantity = get_balance(account_id=account_id, ledger_date=ledger_date)
        return balance_quantity
    else:
        logger.info("Posting new balance for date: %s", ledger_date)
        now = datetime.now(pytz.timezone('Asia/Singapore'))
        today = now.date().strftime("%Y-%m-%d")
        logger.info("Today is: %s", today)
        if ledger_date != today:
            json_body = app.current_request.json_body
            balance_quantity = Decimal(json_body.get('balance_quantity'))
        else: 
            # Remove hardcoded customer id
            logger.info("Requesting latest balance from Ledger Operations")
            details = requests.get(balance_api).json()
            balance_quantity = Decimal(details['data']['primary_ledger_data']['amount']).quantize(Decimal("0.0001"))
            logger.info("Latest balance: %s", balance_quantity)
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

# GET CUSTOMER DETAILS
@app.route('/customers/{customer_id}', methods=['GET'], cors=True)
def get_customer(customer_id):
    customer = ledgers.get_item(
        Key={'customer_id': customer_id}
    )
    customer = customer['Item']
    return customer

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
    crediting_amount = balance * crediting_rate
    logger.info("Crediting Amount: %s", crediting_amount)
    insert_charge(account_id=account_id, ledger_date=ledger_date, charge_type='credit', charge_value=crediting_amount)
    # Interledger transfer from singlife to charges
    details = get_customer(prototype_customer_id)
    interledger_quantity = crediting_amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    payload = {'from_ledger': main_charge_ledger, 'to_ledger': details['charge_ledger'], 'amount': interledger_quantity}
    r = requests.post(transfer_api, data=payload)
    logger.info(r.text)
    return crediting_amount

# Process EOD
@app.route('/eom/{account_id}/{ledger_month}', methods=['GET', 'POST'], cors=True)
def process_eom(account_id, ledger_month):
    logger.info("Processing EOD for account_id: %s for month: %s", account_id, ledger_month)
    # Get all charges for month
    # This is lame - do it properly
    start_date = ledger_month + '-01'
    year, month = ledger_month.split('-')
    end_date = ledger_month + '-' + str(calendar.monthrange(int(year), int(month))[1])
    response = charges.query(
        KeyConditionExpression=Key('account_id').eq(account_id) & Key('ledger_date').between(start_date, end_date)
    )
    # Sum up charges
    total_quantity = sum([Decimal(item['charge_value']) for item in response['Items']])
    # If it's a POST, also write the result back
    if app.current_request.method == 'POST':
        insert_charge(account_id=account_id, ledger_date=end_date, charge_type='credit_settle', charge_value=-1 * total_quantity)
        # Interledger transfer from charges to main
        details = get_customer(prototype_customer_id)
        interledger_quantity = total_quantity.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        payload = {'from_ledger': details['charge_ledger'], 'to_ledger': details['main_ledger'], 'amount': interledger_quantity}
        r = requests.post(transfer_api, data=payload)
        logger.info(r.text)
    logger.info("Total Quantity is: %s", total_quantity)
    return response
