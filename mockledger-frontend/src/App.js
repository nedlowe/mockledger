import React, { Component } from 'react';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col'
import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import logo from './logo.jpg';
import './App.css';
import BalanceGrid from './components/balance_grid';
import ChargeGrid from './components/charge_grid';


const api_path = 'https://alzrnmc09j.execute-api.ap-southeast-1.amazonaws.com/api/'

const account_id = '937501964'

const monthly_balances_api = api_path + 'balances/' + account_id + '?month=2019-03'
const monthly_charges_api = api_path + 'eom/' + account_id + '/2019-03'
const charge_post_api = api_path + 'eod/' + account_id + '/'
const balance_update_api = api_path + 'balances/' + account_id + '/'

class App extends Component {

  constructor() {
    super();
    this.state = {
      balances_rows: [],
      charges_rows: [],
      ledger_date: '2019-03-27',
      charge_calc_date: '2019-03-27',
      temp_balance: '123'
    };
  }

  callMonthlyBalancesApi() {
    fetch(monthly_balances_api)
      .then((result) => {
        return result.json();
      }).then((jsonResult) => {
        // Do something with the result
        console.log(jsonResult);
        this.setState({
          balances_rows: jsonResult.Items
        });
      })
  }

  callMonthlyChargesApi() {
    fetch(monthly_charges_api)
      .then((result) => {
        return result.json();
      }).then((jsonResult) => {
        // Do something with the result
        console.log(jsonResult);
        this.setState({
          charges_rows: jsonResult.Items
        });
      })
  }

  setChargesForDay() {
    fetch(charge_post_api + this.state.charge_calc_date, {
      method: 'POST'
    })
      .then((result) => {
        return result.json();
      }).then((jsonResult) => {
        // Do something with the result
        console.log(jsonResult);
      })
  }

  setEOM() {
    fetch(monthly_charges_api, {
      method: 'POST'
    })
      .then((result) => {
        return result.json();
      }).then((jsonResult) => {
        // Do something with the result
        console.log(jsonResult);
      })
  }


  setBalanceForDay() {
    fetch(balance_update_api + this.state.ledger_date, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        balance_quantity: this.state.temp_balance
      })
    })
      .then((result) => {
        return result.json();
      }).then((jsonResult) => {
        // Do something with the result
        console.log(jsonResult);
      })
  }

  updateLedgerDateValue(evt) {
    this.setState({
      ledger_date: evt.target.value
    });
  }
  updateChargeCalcDateValue(evt) {
    this.setState({
      charge_calc_date: evt.target.value
    });
  }
  updateTempBalanceValue(evt) {
    this.setState({
      temp_balance: evt.target.value
    });
  }

  render() {
    return (
      <div className="App">
        <div>
          <img src={logo} alt="logo" />
        </div>
        <Container>
          <Row className='top-buffer'>
            <Col>
              <Button onClick={() => this.callMonthlyBalancesApi()}>
                Click here to get balances
              </Button>
            </Col>
          </Row>
          <Row className='top-buffer'>
            <Col>
              <BalanceGrid
                rows={this.state.balances_rows}
              />
            </Col>
          </Row>
          <Row className='top-buffer'>
            <Col>
              <Button onClick={() => this.callMonthlyChargesApi()}>
                Click here to get charges
        </Button>
            </Col>
          </Row>
          <Row className='top-buffer'>
            <Col>
              <ChargeGrid
                rows={this.state.charges_rows}
              />
            </Col>
          </Row>
          <Row className='top-buffer'>
            <Col>
              <input name='ledger_date' value={this.state.ledger_date} onChange={evt => this.updateLedgerDateValue(evt)} />
              <input name='temp_balance' value={this.state.temp_balance} onChange={evt => this.updateTempBalanceValue(evt)} />
              <Button onClick={() => this.setBalanceForDay()}>
                Click here to get balance for day and update ledger
        </Button>
            </Col>
          </Row>
          <Row className='top-buffer'>
            <Col>
              <input name='charge_calc_date' value={this.state.charge_calc_date} onChange={evt => this.updateChargeCalcDateValue(evt)} />
              <Button onClick={() => this.setChargesForDay()}>
                Calculate charges for date
              </Button>
            </Col>
          </Row>
          <Row className='top-buffer'>
            <Col>
              <Button onClick={() => this.setEOM()}>
                End of Month Process
              </Button>
            </Col>
          </Row>
        </Container>
      </div>
    );
  }
}

export default App;
