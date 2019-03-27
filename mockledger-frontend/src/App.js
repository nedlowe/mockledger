import React, { Component } from 'react';
import logo from './logo.jpg';
import './App.css';
import BalanceGrid from './components/balance_grid';
import ChargeGrid from './components/charge_grid';


const api_path = 'https://alzrnmc09j.execute-api.ap-southeast-1.amazonaws.com/api/'

const monthly_balances_api = api_path + 'balances/405388793?month=2019-03'
const monthly_charges_api = api_path + 'eom/405388793/2019-03'
const charge_post_api = api_path + 'eod/405388793/'
const balance_update_api = api_path + 'balances/405388793/'

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

  setBalanceForDay() {
    fetch(balance_update_api + this.state.ledger_date, {
      method: 'POST'})
      .then((result) => {
        return result.json();
      }).then((jsonResult) => {
        // Do something with the result
        console.log(jsonResult);
      })
  }

  setChargesForDay() {
    fetch(charge_post_api + this.state.charge_calc_date, {
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
        <div>
          <button onClick={() => this.callMonthlyBalancesApi()}>
            Click here to get balances
        </button>
          <BalanceGrid
            rows={this.state.balances_rows}
          />
        </div>
        <div>
          <input name='ledger_date' value={this.state.ledger_date} onChange={evt => this.updateLedgerDateValue(evt)} />
          <input name='temp_balance' value={this.state.temp_balance} onChange={evt => this.updateTempBalanceValue(evt)} />
          <button onClick={() => this.setBalanceForDay()}>
            Click here to get balance for day and update ledger
        </button>
        </div>
        <div>
          <button onClick={() => this.callMonthlyChargesApi()}>
            Click here to get charges
        </button>
          <ChargeGrid
            rows={this.state.charges_rows}
          />
        </div>
        <div>
          <input name='charge_calc_date' value={this.state.charge_calc_date} onChange={evt => this.updateChargeCalcDateValue(evt)} />
          <button onClick={() => this.setChargesForDay()}>
            Calculate charges for date
        </button>
        </div>
      </div>
    );
  }
}

export default App;
