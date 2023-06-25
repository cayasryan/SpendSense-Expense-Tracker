# Dash related dependencies
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import pandas as pd
from datetime import date

from app import app
from apps import commonmodules as cm
from apps import dbconnect as db

from urllib.parse import urlparse, parse_qs

# To solve psycopg having trouble adapting numpy.int64
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
register_adapter(np.int64, AsIs)

# Helper function to find trans_id
def find_trans_id(acc_id, trans_type, trans_date, trans_amt, trans_notes):
    if not trans_notes: #trans_notes is empty
        sql = """
            SELECT trans_id FROM transactions
            WHERE acc_id = %s AND trans_type = %s AND trans_date = %s AND trans_amt = %s AND trans_notes IS NULL
                AND trans_delete_ind = False
            ORDER BY trans_last_updated DESC
        """
        values = [acc_id, trans_type, trans_date, trans_amt]
    else:
        sql = """
            SELECT trans_id FROM transactions
            WHERE acc_id = %s AND trans_type = %s AND trans_date = %s AND trans_amt = %s AND trans_notes = %s
                AND trans_delete_ind = False
            ORDER BY trans_last_updated DESC
        """
        values = [acc_id, trans_type, trans_date, trans_amt, trans_notes]
    col = ['trans_id']

    df = db.querydatafromdatabase(sql, values, col)

    return df['trans_id'][0]



layout = html.Div(
    [
        html.Div(
            [
                dcc.Location(id='transactions-url', refresh=True),
                dcc.Store(id='transactions_toedit', storage_type='memory', data=0),
                dcc.Store(id='transaction-updated', storage_type='memory', data=0),
                dcc.Store(id='old_trans_amt', storage_type='memory', data=None),
                dcc.Store(id='old_trans_type', storage_type='memory', data=None)
            ],
        ),

        dbc.Card(
            [
                dbc.CardHeader(
                    html.H3('My Transactions')
                ),
                dbc.CardBody(
                    [
                        html.Div( # Add Transaction Btn
                            [
                                dbc.Button("Add Transaction", href='transactions?mode=add', id='add_trans_btn')
                            ]
                        ),
                        html.Div(
                            id = "trans_list",
                            style = {'margin-top': '1em'}
                        )
                    ]
                )
            ]
        ),

        dbc.Modal( # Add/Edit Transaction Modal
            [
                dbc.ModalHeader(dbc.ModalTitle(id="trans_modal_title"), close_button=False),
                dbc.ModalBody(
                    [
                        dbc.Row(
                            [
                                dbc.Label("Account"),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='trans_acc_name',
                                        placeholder='Select Account'
                                    ),
                                    width=5
                                )
                            ],
                            className='mb-3' # add 1em bottom margin
                        ),

                        dbc.Row(
                            [
                                dbc.Label("Transaction Type"),
                                dcc.RadioItems(["Expense","Income"], "Expense", 
                                               inline=True, id="trans_type_radio",
                                               style={"display": "flex", "flex-direction": "row"},
                                               labelStyle={"margin-right": "20px"},
                                               inputStyle={"margin-right": "5px"})
                            ],
                            className="mb-3",
                        ),


                        #Input for Transaction Date
                        dbc.Row(
                            [
                                dbc.Label("Transaction Date"),
                                dcc.DatePickerSingle(
                                    id = "trans_date",
                                    max_date_allowed = date.today(),
                                    date=date.today(),
                                ),
                            ],
                            className="mb-3"
                        ),


                        dbc.Row(
                            [
                                dbc.Label("Transaction Amount"),
                                dbc.Input(
                                    id="trans_amt_input",
                                    type="number", min = 0,
                                    placeholder="Enter transaction amount",
                                    step=0.01,
                                ),
                                dbc.FormFeedback("Invalid amount.", type = "invalid"),
                            ],
                            className="mb-3",
                        ),

                        dbc.Row(
                            [
                                dbc.Label("Transaction Notes"),
                                dbc.Input(id="trans_notes", type="text", placeholder="Enter transaction details (optional)", maxlength=256),
                                dbc.FormFeedback("Exceeded character limit.", type = "invalid"),
                            ],
                            className="mb-3",
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button("Submit", id='trans_modal_submit', color='primary', className='me-1', n_clicks=0),
                        dbc.Button("Close", id='trans_modal_close', href='transactions', color='secondary', className='me-1', n_clicks=0)
                    ]
                )
            ],
            id='trans_modal',
            keyboard=False,
            backdrop='static' 
        ),

        dbc.Modal(  #Notification Modal
                            [
                                dbc.ModalHeader(dbc.ModalTitle(id="trans_modal_notifs_header"), close_button=False),
                                dbc.ModalBody(id="trans_modal_notifs_content"),
                                dbc.ModalFooter(
                                    [
                                        dbc.Button(
                                            "Close",
                                            id="trans_modal_notifs_close", href='transactions', className="me-2", n_clicks=0
                                        )
                                    ]
                                ),
                            ],
                            id="trans_modal_notifs",
                            is_open=False,
                            keyboard=False,
                            backdrop='static'
                        ),

        dbc.Modal(  #Delete Modal
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Are you sure?"), close_button=False),
                                dbc.ModalBody("Please confirm deletion. This action cannot be undone."),
                                dbc.ModalFooter(
                                    [
                                        dbc.Button(
                                            "Delete",
                                            id="trans_delete_modal_delete", color="danger", className="me-2", n_clicks=0
                                        ),
                                        dbc.Button(
                                            "Close",
                                            id="trans_delete_modal_close", href='transactions', className="me-2", n_clicks=0
                                        )
                                    ]
                                ),
                            ],
                            id="trans_delete_modal",
                            is_open=False,
                            keyboard=False,
                            backdrop='static'
                        ),
    ]
)

@app.callback(
    [
        Output("trans_acc_name", 'options')
    ],
    [
        Input("transactions-url", 'pathname')
    ],
    [
        State("currentuserid",'data')
    ]
)
def populate_accounts(pathname, userid):
    if pathname == '/transactions':
        sql = """
        SELECT accounts.acc_name as label, accounts.acc_id as value
        FROM accounts LEFT JOIN useraccounts
            ON accounts.acc_id = useraccounts.acc_id
        WHERE user_id = %s AND acc_delete_ind = False
        ORDER BY accounts.acc_name
        """
        values = [userid]
        cols = ['label', 'value']

        df = db.querydatafromdatabase(sql, values, cols)

        account_options = df.to_dict('records')
    else:
        raise PreventUpdate

    return [account_options]

# app callback when search changes
@app.callback(
    [
        Output('transactions_toedit','data'),
        Output('trans_delete_modal', 'is_open')
    ],
    [
        Input('transactions-url','search'),
        Input('trans_delete_modal_close', 'n_clicks'),
        Input("trans_modal_notifs_close",'n_clicks'),
        Input("trans_modal_close", 'n_clicks')
    ],
    [
        State('transactions-url','pathname')
    ]
)
def trans_edit_delete_indicator(search, delete_close_btn, notif_close_btn, trans_close_btn, pathname):
    
    ctx = dash.callback_context
    if ctx.triggered:

        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        if eventid == "trans_delete_modal_close" and delete_close_btn:
            return [0, False]
        
        elif eventid == "trans_modal_notifs_close" and notif_close_btn:
            return [0, False]
        
        elif eventid == "trans_modal_close" and trans_close_btn:
            return [0, False]
        
        elif pathname == '/transactions':
            if search:
                parsed = urlparse(search)
                create_mode = parse_qs(parsed.query)['mode'][0]
                to_edit = 1 if create_mode == 'edit' else 0
                open_modal = True if create_mode == 'delete' else False

                return [to_edit, open_modal]
            else:
                raise PreventUpdate
        else:
            raise PreventUpdate

    else:
        raise PreventUpdate

# app callback to load values on edit mode
@app.callback(
    [
        Output("trans_acc_name", 'value'),
        Output("trans_type_radio", 'value'),
        Output("trans_date", 'date'),
        Output("trans_amt_input", 'value'),
        Output("trans_notes", 'value'),
        Output("old_trans_amt", 'data'),
        Output("old_trans_type", 'data')
    ],
    [
        Input("transactions_toedit", 'modified_timestamp'),
        Input("trans_modal_close", 'n_clicks'),
        Input("trans_modal_notifs_close", 'n_clicks')
    ],
    [
        State("transactions_toedit", 'data'),
        State('transactions-url', 'search'),
    ]
)
def load_transactions(timestamp, close_btn, close_notifs_btn, to_edit, search):

    ctx = dash.callback_context

    if ctx.triggered:
        #print("update trans triggered")
        #print(ctx.triggered)

        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if eventid == "transactions_toedit" and to_edit:
            parsed = urlparse(search)
            trans_id = parse_qs(parsed.query)['id'][0]

            sql = """
                SELECT acc_id, trans_type, trans_date, trans_amt, trans_notes
                FROM transactions
                WHERE trans_id = %s
            """
            values = [trans_id]
            col = ['acc_id', 'trans_type', 'trans_date', 'trans_amt', 'trans_notes']

            df = db.querydatafromdatabase(sql, values, col)

            acc_id = df['acc_id'][0]
            trans_type = df['trans_type'][0]
            trans_date = df['trans_date'][0]
            trans_amt = df['trans_amt'][0]
            trans_notes = df['trans_notes'][0]

            return [acc_id, trans_type, trans_date, trans_amt, trans_notes, trans_amt, trans_type]
        
        elif (eventid == "trans_modal_close" and close_btn) or (eventid == "trans_modal_notifs_close" and close_notifs_btn):
            # restore transaction input values to default
            return [None, "Expense", date.today(), None, None, None, None]
        
        else:
            raise PreventUpdate

    else:
        raise PreventUpdate
    

@app.callback( # Submitting Transaction Form (Add/Edit)
    [
        Output("trans_modal", "is_open"),
        Output("trans_modal_notifs",'is_open'),
        Output("trans_modal_notifs_header",'children'),
        Output("trans_modal_notifs_content",'children'),

        Output("trans_acc_name",'invalid'),
        Output("trans_amt_input",'invalid'),

        Output("transactions-url", 'search'),
    ],
    [
        Input("add_trans_btn", "n_clicks"), 
        Input("trans_modal_close", "n_clicks"),
        Input("trans_modal_submit",'n_clicks'),
        Input("trans_modal_notifs_close",'n_clicks'),
        Input("trans_delete_modal_delete", "n_clicks"),

        Input("transactions_toedit", 'modified_timestamp')
    ],
    [
        State("trans_acc_name", 'value'),
        State("trans_type_radio", 'value'),
        State("trans_date", 'date'),
        State("trans_amt_input", 'value'),
        State("trans_notes", 'value'),

        State("currentuserid",'data'),
        State('transactions-url', 'search'),
        State("transactions_toedit", 'data'),
        State("old_trans_amt", 'data'),
        State("old_trans_type", 'data')
    ]
)
def update_trans(addtrans_btn, formclose_btn,submit_btn,notif_close_btn, delete_btn, to_edit_time,
               acc_id,trans_type,trans_date, trans_amt, trans_notes, user_id, search, to_edit, old_trans_amt, old_trans_type):

    ctx = dash.callback_context

    if ctx.triggered:
        #print("update trans triggered")
        #print(ctx.triggered)

        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        # #print(eventid)

        if eventid == "trans_modal_notifs_close" and notif_close_btn:
            # #print("Notifs close button")

            #print("transaction modal notifs close triggered")

            return [False,False,None,None,False,False,None]
        
        elif eventid == "add_trans_btn" and addtrans_btn:
            return [True,False,None,None,False,False,search]

        elif eventid == "trans_modal_close" and formclose_btn:

            #print("transaction modal close triggered")
            return [False,False,None,None,False,False,None]
        
        elif eventid == "trans_delete_modal_delete" and delete_btn:
            # delete transaction and open trans notifs modal
            parsed = urlparse(search)
            trans_id = parse_qs(parsed.query)['id'][0]

            sql = '''
                UPDATE transactions
                SET trans_delete_ind = %s, trans_last_updated = now()
                WHERE trans_id = %s
            '''

            values = [True,trans_id]
            db.modifydatabase(sql,values)

            #query transaction details
            sqlcode4 = """
                SELECT acc_id, trans_type, trans_amt FROM transactions WHERE trans_id = %s
            """
            valuescode4 = [trans_id]
            cols4 = ['acc_id', 'trans_type','trans_amt']

            df = db.querydatafromdatabase(sqlcode4,valuescode4,cols4)
            acc_id_deletedtrans = df['acc_id'][0]
            trans_type_deletedtrans = df['trans_type'][0]
            trans_amt_deletedtrans = df['trans_amt'][0]

            #update account balance
            if trans_type_deletedtrans == "Income":
                trans_diff_deletedtrans = -trans_amt_deletedtrans
            else:
                trans_diff_deletedtrans = trans_amt_deletedtrans

            sqlcode3 = """
                            UPDATE accounts
                            SET acc_bal = acc_bal + %s, acc_last_updated = now()
                            WHERE acc_id = %s
                        """
            valuescode3 = [trans_diff_deletedtrans, acc_id_deletedtrans]
            db.modifydatabase(sqlcode3,valuescode3)

            modal_open = True
            modal_header = "Deleted Successfully!"
            modal_content = "Your transaction details have been successfully deleted."

            return [False, modal_open, modal_header, modal_content, False, False, None]
        
        elif eventid == "transactions_toedit" and to_edit:
            #open transaction modal
            return [True, False, None, None, False, False, search]


        elif eventid == "trans_modal_submit" and submit_btn:
            # #print("Form Submit Button")
            
            try:

                # check for invalid inputs
                if not acc_id and not trans_amt:
                    return [True, False, None, None, True, True, search]
                if not acc_id:
                    return [True, False, None, None, True, False, search]
                if not trans_amt:
                    return [True, False, None, None, False, True, search]

                parsed = urlparse(search)
                create_mode = parse_qs(parsed.query)['mode'][0]

                # add trans to transactions table 
                if create_mode == 'add':

                    if not trans_notes: # if trans_notes is empty
                        #print('empty trans_notes',trans_notes)
                        sql1 = '''
                                    INSERT INTO transactions (acc_id, trans_type, trans_date, trans_amt)
                                    VALUES (%s, %s, %s, %s)
                                '''
                            
                        values1 = [acc_id, trans_type,trans_date, trans_amt]
                    else:
                        sql1 = '''
                                    INSERT INTO transactions (acc_id, trans_type, trans_date, trans_amt, trans_notes)
                                    VALUES (%s, %s, %s, %s, %s)
                                '''
                            
                        values1 = [acc_id, trans_type,trans_date, trans_amt, trans_notes]
                    db.modifydatabase(sql1, values1)


                    # add trans to usertransactions table
                    trans_id = find_trans_id(acc_id, trans_type, trans_date, trans_amt, trans_notes)

                    sql2 = '''
                                INSERT INTO usertransactions (user_id, trans_id)
                                VALUES (%s, %s)
                            '''
                        
                    values2 = [user_id, trans_id]
                    db.modifydatabase(sql2, values2)


                    # Update acc bal
                    if trans_type == "Income":
                        sqlcode = """
                            UPDATE accounts
                            SET acc_bal = acc_bal + %s, acc_last_updated = now()
                            WHERE acc_id = %s
                        """

                        valuescode = [trans_amt, acc_id]
                    
                    else:
                        sqlcode = """
                            UPDATE accounts
                            SET acc_bal = acc_bal - %s, acc_last_updated = now()
                            WHERE acc_id = %s
                        """

                        valuescode = [trans_amt, acc_id]

                    db.modifydatabase(sqlcode, valuescode)



                    modal_open = True
                    modal_header = "Saved Sucessfully!"
                    modal_content = "Your transaction details have been successfully updated."

                elif create_mode == 'edit':
                    # IF BALANCE IS UPDATED, A NEW TRANSACTION MUST BE AUTOMATICALLY CREATED

                    parsed = urlparse(search)
                    trans_id = parse_qs(parsed.query)['id'][0]

                    if not trans_notes: #trans_notes is empty
                        sql3 = """
                            UPDATE transactions
                            SET
                                acc_id = %s,
                                trans_type = %s,
                                trans_date = %s,
                                trans_amt = %s,
                                trans_notes = NULL,
                                trans_last_updated = now()
                            WHERE
                                trans_id = %s
                        """

                        values3 = [acc_id, trans_type, trans_date, trans_amt, trans_id]
                    else:
                        sql3 = """
                            UPDATE transactions
                            SET
                                acc_id = %s,
                                trans_type = %s,
                                trans_date = %s,
                                trans_amt = %s,
                                trans_notes = %s,
                                trans_last_updated = now()
                            WHERE
                                trans_id = %s
                        """

                        values3 = [acc_id, trans_type, trans_date, trans_amt, trans_notes, trans_id]
                    db.modifydatabase(sql3, values3)



                    if trans_amt != old_trans_amt or trans_type != old_trans_type: #Check if trans_amt or trans_type has been edited
                        # reverse old transaction from acc_bal and add new transaction to acc_bal
                        
                        trans_diff = 0
                        if trans_amt != old_trans_amt and trans_type != old_trans_type: #both have been edited
                            if trans_type == "Income": #old trans type was an expense
                                trans_diff = old_trans_amt + trans_amt
                            else:
                                trans_diff = -old_trans_amt - trans_amt
                        elif trans_amt != old_trans_amt: #only trans_amt has been edited
                            if trans_type == "Income":
                                trans_diff = trans_amt - old_trans_amt
                            else:
                                trans_diff = old_trans_amt - trans_amt
                        elif trans_type != old_trans_type: #only trans_type has been edited
                            if trans_type == "Income":
                                trans_diff = 2*trans_amt
                            else:
                                trans_diff = -2*trans_amt

                        sqlcode2 = """
                            UPDATE accounts
                            SET acc_bal = acc_bal + %s, acc_last_updated = now()
                            WHERE acc_id = %s
                        """
                        valuescode2 = [trans_diff,acc_id]
                        db.modifydatabase(sqlcode2,valuescode2)
                        

                    modal_open = True
                    modal_header = "Edited Successfully!"
                    modal_content = "Your transaction details have been successfully updated."

                return [False, modal_open, modal_header, modal_content, False, False, None]
            
            except Exception as e:
                print(e)
                modal_open = True
                modal_header = "Error!"
                modal_content = "There has been an unexpected error. Please try again."

                return [False, modal_open, modal_header, modal_content, False, False, None]
        else:
            raise PreventUpdate                

    else:
        raise PreventUpdate


@app.callback(
    Output('transaction-updated', 'data'), 
    Input("trans_modal_notifs_close",'n_clicks')
)
def trans_update_indicator(close_btn):
    ctx = dash.callback_context
    #print("Transaction update triggered.")
    #print(ctx.triggered)
    if ctx.triggered:
        return True 
    else:
        #print("Prevented Update.")
        raise PreventUpdate


@app.callback(
    Output('trans_list', 'children'),
    [Input('transactions-url','pathname'), Input('transaction-updated', 'data')],
    State('currentuserid','data')
)
def display_trans(pathname, updated, user_id):
    if pathname == '/transactions':
        #print("Display transactions triggered.")

        sql = ''' 
                SELECT T.trans_id, A.acc_name, trans_type, TO_CHAR(date(trans_date), 'Month dd, yyyy'), trans_amt, trans_notes
                FROM usertransactions UT LEFT JOIN transactions T
                    ON UT.trans_id = T.trans_id
                    LEFT JOIN accounts A ON T.acc_id = A.acc_id
                WHERE user_id = %s AND trans_delete_ind = False
                ORDER BY trans_date DESC, trans_last_updated DESC
            '''
        
        values = [user_id]
        cols = ['ID', 'Account','Type','Date','Amount','Notes']

        df = db.querydatafromdatabase(sql, values, cols)

        if not df.empty:
            # Adding Edit button:

            buttons = []
            for trans_id in df['ID']:
                buttons += [
                html.Div(
                    [
                        dbc.Button('Edit', 
                                href=f'transactions?mode=edit&id={trans_id}',
                                size='sm', color='warning',
                                className = "me-2"),
                        dbc.Button('Delete', 
                                href=f'transactions?mode=delete&id={trans_id}',
                                size='sm', color='danger',
                                className = "me-2"),
                    ],
                    style={'text-align': 'center'},
                ) 
                ]
            df['Action'] = buttons

            # remove the column ID before turning into a table 
            df = df[['Account','Type','Date','Amount','Notes', 'Action']]
            df['Amount'] = ["{:,.2f}".format(x) for x in df['Amount'].tolist()]


            table = dbc.Table.from_dataframe(df, striped=True, bordered=True, 
                                            hover=True, size='sm')
            return [table]
        else:
            return ['No transactions yet. Click "Add Transaction" to add your first one.']

    else:
        raise PreventUpdate
