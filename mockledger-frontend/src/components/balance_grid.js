import React, { Component } from 'react';
import ReactDataGrid from 'react-data-grid';

const balance_columns = [
    { key: 'ledger_date', name: 'Ledger Date' },
    { key: 'balance_quantity', name: 'Balance' }];

export default class BalanceGrid extends Component {

    render() {
        return (
            <ReactDataGrid
            columns={balance_columns}
            rowGetter={i => this.props.rows[i]}
            rowsCount={this.props.rows.length}
             />
        )
    }
}
