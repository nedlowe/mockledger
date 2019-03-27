import React, { Component } from 'react';
import ReactDataGrid from 'react-data-grid';

const charge_columns = [
    { key: 'ledger_date', name: 'Ledger Date' },
    { key: 'charge_type', name: 'Charge Type' },
    { key: 'charge_value', name: 'Value' }];

export default class ChargeGrid extends Component {

    render() {
        return (
            <ReactDataGrid
            columns={charge_columns}
            rowGetter={i => this.props.rows[i]}
            rowsCount={this.props.rows.length}
             />
        )
    }
}
