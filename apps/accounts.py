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

# Helper function to find acc_id
def find_acc_id(acc_name, acc_type, acc_bal):
    sql = """
        SELECT acc_id FROM accounts
        WHERE acc_name = %s AND acc_type = %s AND acc_bal = %s 
            AND acc_delete_ind = False
        ORDER BY acc_last_updated DESC
    """
    values = [acc_name, acc_type, acc_bal]
    col = ['acc_id']

    df = db.querydatafromdatabase(sql, values, col)

    return df['acc_id'][0]

# Helper function to find trans_id
def find_trans_id(acc_id, trans_type, trans_date, trans_amt, trans_notes):
    print("finding trans_id")
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
                dcc.Location(id='accounts-url', refresh=True),
                dcc.Store(id='accounts_toedit', storage_type='memory', data=0),
                dcc.Store(id='account-updated', storage_type='memory', data=0),
                dcc.Store(id='old_acc_bal', storage_type='memory', data=None)

            ],
        ),

        dbc.Card(
            [
                dbc.CardHeader(
                    html.H3('My Accounts')
                ),
                dbc.CardBody(
                    [
                        html.Div( # Add Account Btn
                            [
                                dbc.Button("Add Account", href='accounts?mode=add', id='add_acc_btn')
                            ]
                        ),
                        html.Div(
                            id = "acc_list",
                            style = {'margin-top': '1em'}
                        )
                    ]
                )
            ]
        ),

        dbc.Modal( # Add/Edit Account Modal
            [
                dbc.ModalHeader(dbc.ModalTitle(id="acc_modal_title"), close_button=False),
                dbc.ModalBody(
                    [
                        dbc.Row(
                            [
                                dbc.Label("Account Name"),
                                dbc.Input(id="acc_name_input", type="text", placeholder="Enter account name", maxlength=30),
                                dbc.FormFeedback("Invalid input.", type = "invalid"),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Label("Account Type"),
                                dcc.RadioItems(["Cash","Savings","Checking"], "Cash", 
                                               inline=True, id="acc_type_radio",
                                               style={"display": "flex", "flex-direction": "row"},
                                               labelStyle={"margin-right": "20px"},
                                               inputStyle={"margin-right": "5px"})
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Label("Current Balance"),
                                dbc.Input(
                                    id="acc_bal_input",
                                    type="number", min = 0,
                                    placeholder="Enter current balance",
                                    step=0.01,
                                ),
                                dbc.FormFeedback("Invalid amount.", type = "invalid"),
                            ],
                            className="mb-3",
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button("Submit", id='acc_modal_submit', color='primary', className='me-1', n_clicks=0),
                        dbc.Button("Close", id='acc_modal_close', href='accounts', color='secondary', className='me-1', n_clicks=0)
                    ]
                )
            ],
            id='acc_modal',
            keyboard=False,
            backdrop='static' 
        ),

        dbc.Modal(  #Notification Modal
                            [
                                dbc.ModalHeader(dbc.ModalTitle(id="acc_modal_notifs_header"), close_button=False),
                                dbc.ModalBody(id="acc_modal_notifs_content"),
                                dbc.ModalFooter(
                                    [
                                        dbc.Button(
                                            "Close",
                                            id="acc_modal_notifs_close", href='accounts', className="me-2", n_clicks=0
                                        )
                                    ]
                                ),
                            ],
                            id="acc_modal_notifs",
                            is_open=False,
                            keyboard=False,
                            backdrop='static'
                        ),

        dbc.Modal(  #Delete Modal
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Are you sure?"), close_button=False),
                                dbc.ModalBody("Please confirm account deletion. This action cannot be undone."),
                                dbc.ModalFooter(
                                    [
                                        dbc.Button(
                                            "Delete",
                                            id="acc_delete_modal_delete", color="danger", className="me-2", n_clicks=0
                                        ),
                                        dbc.Button(
                                            "Close",
                                            id="acc_delete_modal_close", href='accounts', className="me-2", n_clicks=0
                                        )
                                    ]
                                ),
                            ],
                            id="acc_delete_modal",
                            is_open=False,
                            keyboard=False,
                            backdrop='static'
                        ),
    ]
)

# app callback when search changes
@app.callback(
    [
        Output('accounts_toedit','data'),
        Output('acc_delete_modal', 'is_open')
    ],
    [
        Input('accounts-url','search'),
        Input('acc_delete_modal_close', 'n_clicks'),
        Input("acc_modal_notifs_close",'n_clicks'),
        Input("acc_modal_close", 'n_clicks')
    ],
    [
        State('accounts-url','pathname')
    ]
)
def acc_edit_delete_indicator(search, delete_close_btn, notif_close_btn, acc_close_btn, pathname):
    
    ctx = dash.callback_context
    if ctx.triggered:
        #print("Acc edit delete indicator triggered")
        #print(ctx.triggered)

        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        if eventid == "acc_delete_modal_close" and delete_close_btn:
            return [0, False]
        
        elif eventid == "acc_modal_notifs_close" and notif_close_btn:
            return [0, False]
        
        elif eventid == "acc_modal_close" and acc_close_btn:
            return [0, False]
        
        elif pathname == '/accounts':
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
        Output("acc_name_input", 'value'),
        Output("acc_type_radio", 'value'),
        Output("acc_bal_input", 'value'),
        Output('old_acc_bal', 'data')
    ],
    [
        Input("accounts_toedit", 'modified_timestamp'),
        Input("acc_modal_close", 'n_clicks'),
        Input("acc_modal_notifs_close", 'n_clicks')
    ],
    [
        State("accounts_toedit", 'data'),
        State('accounts-url', 'search'),
    ]
)
def load_accounts(timestamp, close_btn, close_notifs_btn, to_edit, search):

    ctx = dash.callback_context

    if ctx.triggered:
        #print("update acc triggered")
        #print(ctx.triggered)

        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if eventid == "accounts_toedit" and to_edit:
            parsed = urlparse(search)
            acc_id = parse_qs(parsed.query)['id'][0]

            sql = """
                SELECT acc_name, acc_type, acc_bal
                FROM accounts
                WHERE acc_id = %s
            """
            values = [acc_id]
            col = ['acc_name', 'acc_type', 'acc_bal']

            df = db.querydatafromdatabase(sql, values, col)

            acc_name = df['acc_name'][0]
            acc_type = df['acc_type'][0]
            acc_bal = df['acc_bal'][0]

            return [acc_name, acc_type, acc_bal, acc_bal]
        
        elif (eventid == "acc_modal_close" and close_btn) or (eventid == "acc_modal_notifs_close" and close_notifs_btn):
            # restore account input values to default
            return [None, "Cash", None, None]
        
        else:
            raise PreventUpdate

    else:
        raise PreventUpdate



@app.callback( # Submitting Account Form (Add/Edit)
    [
        Output("acc_modal", "is_open"),
        Output("acc_modal_notifs",'is_open'),
        Output("acc_modal_notifs_header",'children'),
        Output("acc_modal_notifs_content",'children'),

        Output("acc_name_input",'invalid'),
        Output("acc_bal_input",'invalid'),

        Output("accounts-url", 'search'),
    ],
    [
        Input("add_acc_btn", "n_clicks"), 
        Input("acc_modal_close", "n_clicks"),
        Input("acc_modal_submit",'n_clicks'),
        Input("acc_modal_notifs_close",'n_clicks'),
        Input("acc_delete_modal_delete", "n_clicks"),

        Input("accounts_toedit", 'modified_timestamp')
    ],
    [
        State("acc_name_input",'value'),
        State("acc_type_radio",'value'),
        State("acc_bal_input",'value'),
        State("currentuserid",'data'),
        State('accounts-url', 'search'),
        State("accounts_toedit", 'data'),
        State("old_acc_bal", 'data')
    ]
)
def update_acc(addacc_btn, formclose_btn,submit_btn,notif_close_btn, delete_btn, to_edit_time,
               acc_name,acc_type,acc_bal,user_id, search, to_edit, old_acc_bal):

    ctx = dash.callback_context

    if ctx.triggered:
        #print("update acc triggered")
        #print(ctx.triggered)

        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        # #print(eventid)

        if eventid == "acc_modal_notifs_close" and notif_close_btn:
            # #print("Notifs close button")
            #print("account modal notifs close triggered")

            return [False,False,None,None,False,False,None]
        
        elif eventid == "add_acc_btn" and addacc_btn:
            return [True,False,None,None,False,False,search]

        elif eventid == "acc_modal_close" and formclose_btn:

            #print("account modal close triggered")
            return [False,False,None,None,False,False,None]
        
        elif eventid == "acc_delete_modal_delete" and delete_btn:
            # delete account and open acc notifs modal
            parsed = urlparse(search)
            acc_id = parse_qs(parsed.query)['id'][0]

            sql = '''
                UPDATE accounts
                SET acc_delete_ind = %s, acc_last_updated = now()
                WHERE acc_id = %s
            '''

            values = [True,acc_id]
            db.modifydatabase(sql,values)

            modal_open = True
            modal_header = "Deleted Successfully!"
            modal_content = "Your account details have been successfully deleted."

            return [False, modal_open, modal_header, modal_content, False, False, None]
        
        elif eventid == "accounts_toedit" and to_edit:
            #open account modal
            return [True, False, None, None, False, False, search]


        elif eventid == "acc_modal_submit" and submit_btn:
            # #print("Form Submit Button")
            
            try:

                # check for invalid inputs
                if not acc_name and not acc_bal:
                    return [True, False, None, None, True, True, search]
                if not acc_name:
                    return [True, False, None, None, True, False, search]
                if not acc_bal:
                    return [True, False, None, None, False, True, search]

                parsed = urlparse(search)
                create_mode = parse_qs(parsed.query)['mode'][0]

                # add acc to accounts table 
                if create_mode == 'add':
                    sql1 = '''
                                INSERT INTO accounts (acc_name, acc_type, acc_bal)
                                VALUES (%s, %s, %s)
                            '''
                        
                    values1 = [acc_name, acc_type, acc_bal]
                    db.modifydatabase(sql1, values1)


                    # add acc to useraccounts table
                    acc_id = find_acc_id(acc_name, acc_type, acc_bal)

                    sql2 = '''
                                INSERT INTO useraccounts (user_id, acc_id)
                                VALUES (%s, %s)
                            '''
                        
                    values2 = [user_id, acc_id]
                    db.modifydatabase(sql2, values2)


                    modal_open = True
                    modal_header = "Saved Sucessfully!"
                    modal_content = "Your account details have been successfully saved."

                elif create_mode == 'edit':
                    parsed = urlparse(search)
                    acc_id = parse_qs(parsed.query)['id'][0]

                    sql3 = """
                        UPDATE accounts
                        SET
                            acc_name = %s,
                            acc_type = %s,
                            acc_bal = %s,
                            acc_last_updated = now()
                        WHERE
                            acc_id = %s
                    """

                    values3 = [acc_name, acc_type, acc_bal, acc_id]
                    db.modifydatabase(sql3, values3)


                    if acc_bal != old_acc_bal: #Check if acc_bal has been edited
                        print("adding a transaction")
                    # Add new transaction to preserve relationship with account balance
                        if old_acc_bal > acc_bal: #make an expense transaction
                            trans_type = "Expense"
                            trans_amt = old_acc_bal - acc_bal
                        elif old_acc_bal < acc_bal: #make an income transaction
                            trans_type = "Income"
                            trans_amt = acc_bal - old_acc_bal

                        print("about to insert into transactions table")    
                        sqlcode3 = """
                            INSERT INTO transactions (acc_id, trans_type, trans_date, trans_amt, trans_notes)
                            VALUES (%s, %s, %s, %s, %s)
                        """
                        valuescode3 = [acc_id,trans_type,date.today(),trans_amt,"Update account balance"]
                        db.modifydatabase(sqlcode3,valuescode3)

                        print("about to find trans_id")

                        #Update usertransactions table
                        trans_id = find_trans_id(acc_id, trans_type, date.today(),trans_amt,"Update account balance")

                        sqlcode2 = '''
                                INSERT INTO usertransactions (user_id, trans_id)
                                VALUES (%s, %s)
                            '''
                        
                        valuescode2 = [user_id, trans_id]
                        db.modifydatabase(sqlcode2, valuescode2)


                    modal_open = True
                    modal_header = "Edited Successfully!"
                    modal_content = "Your account details have been successfully updated. If you updated the account's balance, a new transaction will be added to reflect this change."

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
    Output('account-updated', 'data'), 
    Input("acc_modal_notifs_close",'n_clicks')
)
def acc_update_indicator(close_btn):
    ctx = dash.callback_context
    #print("Account update triggered.")
    #print(ctx.triggered)
    if ctx.triggered:
        return True 
    else:
        #print("Prevented Update.")
        raise PreventUpdate


@app.callback(
    Output('acc_list', 'children'),
    [Input('accounts-url','pathname'), Input('account-updated', 'data')],
    State('currentuserid','data')
)
def display_accs(pathname, updated, user_id):
    if pathname == '/accounts':
        #print("Display accounts triggered.")

        sql = ''' 
                SELECT A.acc_id, acc_name, acc_type, acc_bal 
                FROM useraccounts UA LEFT JOIN accounts A
                    ON UA.acc_id = A.acc_id
                WHERE user_id = %s AND acc_delete_ind = False
                ORDER BY acc_name
            '''
        
        values = [user_id]
        cols = ['ID', 'Account Name','Type','Balance']

        df = db.querydatafromdatabase(sql, values, cols)

        if not df.empty:
            # Adding Edit button:

            buttons = []
            for acc_id in df['ID']:
                buttons += [
                html.Div(
                    [
                        dbc.Button('Edit', 
                                href=f'accounts?mode=edit&id={acc_id}',
                                size='sm', color='warning',
                                className = "me-2"),
                        dbc.Button('Delete', 
                                href=f'accounts?mode=delete&id={acc_id}',
                                size='sm', color='danger',
                                className = "me-2"),
                    ],
                    style={'text-align': 'center'},
                ) 
                ]
            df['Action'] = buttons

            # remove the column ID before turning into a table 
            df = df[['Account Name','Type','Balance', 'Action']]
            df['Balance'] = ["{:,.2f}".format(x) for x in df['Balance'].tolist()]


            table = dbc.Table.from_dataframe(df, striped=True, bordered=True, 
                                            hover=True, size='sm')
            return [table]
        else:
            return ['No accounts yet. Click "Add Account" to add your first one.']

    else:
        raise PreventUpdate
