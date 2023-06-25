# Dash related dependencies
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import plotly.graph_objs as go


import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from datetime import date
import datetime as dt

from app import app
from apps import commonmodules as cm
from apps import dbconnect as db

from urllib.parse import urlparse, parse_qs

# To solve psycopg having trouble adapting numpy.int64
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
register_adapter(np.int64, AsIs)

# Helper function to filter df based on selected period and accounts
def filter_df(trans_dict, start_date, end_date, acc_id_list):
    start_date = dt.datetime.strptime(start_date, "%Y-%m-%d").date(),
    end_date = dt.datetime.strptime(end_date, "%Y-%m-%d").date(),

    trans_df = pd.DataFrame(trans_dict["data-frame"])
    trans_df = trans_df[trans_df['AccountID'].isin(acc_id_list)] #filter accounts

    dates = trans_df['Date'].tolist()
    dates_list = [dt.datetime.strptime(date, "%Y-%m-%d").date() for date in dates]

    trans_df['Date'] = dates_list

    filtered_date_df = trans_df[(trans_df['Date'] >= start_date[0]) & (trans_df['Date'] <= end_date[0])]
    return filtered_date_df


layout = html.Div(
    [
        html.Div(
            [
                dcc.Location(id='home-url', refresh=True),
                dcc.Store(id='acc_df'), # to convert to dataframe: acc_df = pd.DataFrame(acc_df["data-frame"])
                dcc.Store(id='trans_df'), # to convert to dataframe: trans_df = pd.DataFrame(trans_df["data-frame"])
            ],
        ),

        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2(id="welcome-msg"),
                            ],
                            width={"size": 3, "order": 1}, 
                        ),
                        
                        dbc.Col(
                            [
                                dbc.Label("Period:",
                                          style={"display": "flex", "align-items": "center", "justify-content": "flex-end"}
                                          ),
                            ],
                            width={"size": 1, "order": 2},
                            style={"text-align": "right"}
                        ),
                        dbc.Col(
                            [
                                dcc.DatePickerRange(
                                    id='dates_covered',
                                    max_date_allowed=date.today(),
                                    end_date = date.today(),
                                    #style={"display": "flex", "align-items": "center"},
                                ),
                            ],
                            width={"size": 3, "order": 3},
                            style={"margin-left": "10px"} 
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Accounts:",
                                          style={"display": "flex", "align-items": "center"}
                                          ),
                            ],
                            width={"size": 1, "order": 4},
                            style={"text-align": "right"}
                        ),
                        dbc.Col(
                            [
                                dcc.Dropdown(
                                    id='home-acc_dropdown',
                                    multi=True,
                                    #style={"display": "flex", "align-items": "center"}
                                )
                            ],
                            width={"size": 3, "order": 5},
                            style={"margin-left": "10px"} 
                        ),
                    ],
                    style={"margin-bottom": "20px"}
                )
            ]
        ),

        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H4("Total Income"), className="text-center"),
                                        dbc.CardBody(
                                            html.H3(id="total_income"),
                                            className="text-center"
                                        )
                                    ],
                                    color = "success", outline = True
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H4("Total Expenses"), className="text-center"),
                                        dbc.CardBody(
                                            html.H3(id="total_expenses"),
                                            className="text-center"
                                        )
                                    ],
                                    color = "danger", outline = True
                                )
                            ]
                        ),
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H4("Net Amount"), className="text-center"),
                                        dbc.CardBody(
                                            html.H3(id="net_gainloss"),
                                            className="text-center"
                                        )

                                    ],
                                    id = 'net_card', outline = True
                                )
                            ]
                        ),
                    ],
                    style={"margin-bottom": "20px"}
                )
            ],
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H3('All Accounts')
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id = "home-acc_list",
                                            style = {'margin-top': '1em'}
                                        )
                                    ]
                                )
                            ]
                        ),
                    ],
                    width={"size": 4, "order": 1},
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H3('Top 5 Expenses')),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id = "top5_exp",
                                            style = {'margin-top': '1em'},
                                        )
                                    ]
                                )
                            ]
                        )
                    ],
                    width={"size": 8, "order": 2},
                )
            ],
            style={"margin-bottom": "20px"}
        ),

        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.H3('All Transactions')
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id = "home-trans_list",
                                            style = {'margin-top': '1em'}
                                        )
                                    ]
                                )
                            ]
                        ),
                    ],
                    width={"size": 12, "order": 1},
                ),

            ]
        )

        
    ]
)

#callback for welcoming the user
@app.callback(
        Output("welcome-msg",'children'),
        Input("home-url",'pathname'),
        State('currentuserid','data')
)
def welcome(pathname,user_id):
    if pathname == '/home' or (pathname == '/' and user_id > 0):
        None
        sql = """
            SELECT username FROM users WHERE user_id = %s
        """
        values = [user_id]
        cols = ['username']

        df = db.querydatafromdatabase(sql,values,cols)
        username = df['username'][0]

        return f'Welcome, {username}!'

    else:
        raise PreventUpdate


#callback: use pathname change as trigger
    #If pathname == '/home' or (pathname == '/' and user_id > 0):
        #load accounts and transactions data

@app.callback(
    [Output('home-trans_list', 'children'), Output('trans_df','data')],
    [Input('home-url','pathname')],
    State('currentuserid','data')
)
def display_trans_home(pathname, user_id):
    if pathname == '/home' or (pathname == '/' and user_id > 0):
        #print("Display transactions triggered.")

        sql = ''' 
                SELECT T.trans_id, A.acc_id, A.acc_name, trans_type, date(trans_date), trans_amt, trans_notes
                FROM usertransactions UT LEFT JOIN transactions T
                    ON UT.trans_id = T.trans_id
                    LEFT JOIN accounts A ON T.acc_id = A.acc_id
                WHERE user_id = %s AND trans_delete_ind = False
                ORDER BY trans_date DESC, trans_last_updated DESC
            '''
        
        values = [user_id]
        cols = ['TransID', 'AccountID', 'Account','Type','Date','Amount','Notes']

        df = db.querydatafromdatabase(sql, values, cols)

        if not df.empty:
            df_dict = {"data-frame": df.to_dict("records")}
            df = df[['Account','Type','Date','Amount','Notes']]


            table = dbc.Table.from_dataframe(df, striped=True, bordered=True, 
                                            hover=True, size='sm')
            
            return [table, df_dict]
        else:
            return ['No transactions yet. Click "Transactions" to add your first one.', None]

    else:
        raise PreventUpdate
    
@app.callback(
    [Output('home-acc_list', 'children'), Output('acc_df','data')],
    [Input('home-url','pathname')],
    State('currentuserid','data')
)
def display_accs(pathname, user_id):
    if pathname == '/home' or (pathname == '/' and user_id > 0):
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
            df_dict = {"data-frame": df.to_dict("records")}
            df = df[['Account Name','Type','Balance']]

            df['Balance'] = ["{:,.2f}".format(x) for x in df['Balance'].tolist()]


            table = dbc.Table.from_dataframe(df, striped=True, bordered=True, 
                                            hover=True, size='sm')
            
            return [table, df_dict]
        else:
            return ['No accounts yet. Click "Accounts" to add your first one.', None]

    else:
        raise PreventUpdate



#callback to populate account options
@app.callback(
    [
        Output("home-acc_dropdown", 'options'),
        Output("home-acc_dropdown", 'value'),
    ],
    [
        Input("home-url", 'pathname')
    ],
    [
        State("currentuserid",'data')
    ]
)
def populate_accounts(pathname, userid):
    if pathname == '/home' or (pathname == '/' and userid > 0):
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

    return [account_options, df['value'].tolist()]




#callback to set min date for period
@app.callback(
    Output("dates_covered",'start_date'),
    Input("trans_df",'modified_timestamp'),
    State("trans_df",'data')
)
def set_start_date(time, trans_dict):
    if trans_dict:
        trans_df = pd.DataFrame(trans_dict["data-frame"])
        dates = trans_df['Date'].tolist()

        dates_list = [dt.datetime.strptime(date, "%Y-%m-%d").date() for date in dates]
        dates_list.sort(reverse=False)

        start_date = dates_list[0]
        return start_date
    else:
        raise PreventUpdate

#callback to update income, expenses, and gain/loss cards
@app.callback(
    [
        Output("total_income", 'children'),
        Output("total_expenses", 'children'),
        Output("net_gainloss", 'children'),
        Output("net_card", 'color')   
    ],
    [
        Input("dates_covered",'start_date'),
        Input("dates_covered", 'end_date'),
        Input("home-acc_dropdown", 'value')
    ],
    [
        State("trans_df",'data'),
    ]
)
def update_totalcards(start_date, end_date, acc_id_list, trans_dict):
    if trans_dict:
        filtered_date_df = filter_df(trans_dict, start_date, end_date, acc_id_list)

        filtered_income_df = filtered_date_df[filtered_date_df['Type'] == "Income"]
        incomes_str_list = filtered_income_df['Amount'].tolist()
        filtered_income_df['Amount'] = [float(x) for x in incomes_str_list]
        total_income = sum(filtered_income_df['Amount'].tolist())

        filtered_expenses_df = filtered_date_df[filtered_date_df['Type'] == "Expense"]
        expenses_str_list = filtered_expenses_df['Amount'].tolist()
        filtered_expenses_df['Amount'] = [float(x) for x in expenses_str_list]
        total_expenses = sum(filtered_expenses_df['Amount'].tolist())

        net_gainloss = total_income - total_expenses
        if net_gainloss < 0:
            color = 'danger'
        elif net_gainloss > 0:
            color = 'success'
        else:
            color = 'warning'


        return [
            "{:,.2f}".format(total_income),
            "{:,.2f}".format(total_expenses),
            "{:,.2f}".format(net_gainloss),
            color
        ]     


    else:
        raise PreventUpdate



#callback to update top 5 biggest expenses
@app.callback(
    [
        Output("top5_exp",'children'),
    ],
    [
        Input("home-url",'pathname'),
        Input("dates_covered", 'start_date'),
        Input("dates_covered", 'end_date'),
        Input("home-acc_dropdown", 'value')
    ],
    [
        State('currentuserid','data'),
        State("trans_df",'data')
    ]
)
def top5_expenses(pathname, start_date, end_date, acc_id_list, user_id, trans_dict):
    if (pathname == '/home' or (pathname == '/' and user_id > 0)) and trans_dict:
        filtered_date_df = filter_df(trans_dict, start_date, end_date, acc_id_list)
        filtered_expenses_df = filtered_date_df[filtered_date_df['Type'] == "Expense"]
        top5_exp_df = filtered_expenses_df.sort_values(by=['Amount'], ascending=False).head(5)

        top5_exp_df = top5_exp_df[['Account', 'Date', 'Amount', 'Notes']]
        top5_exp_df['Amount'] = ["{:,.2f}".format(x) for x in top5_exp_df['Amount'].tolist()]

        table = dbc.Table.from_dataframe(top5_exp_df, striped=True, bordered=True, 
                                            hover=True, size='sm')
        return [table]

    else:
        raise PreventUpdate