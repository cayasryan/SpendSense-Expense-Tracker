# Dash related dependencies
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# To open browser upon running your app
import webbrowser

from app import app
from apps import login, commonmodules as cm
from apps import accounts
from apps import transactions
from apps import home


CONTENT_STYLE = {
    "margin-top": "1em",
    "margin-left": "1em",
    "margin-right": "1em",
    "padding": "1em 1em",
}

app.layout = html.Div(
    [
        dcc.Location(id='index-url', refresh=False),
        dcc.Store(id='currentuserid', data=-1, storage_type = 'session'),
        dcc.Store(id='sessionlogout', data=True, storage_type='session'),

        html.Div(cm.navbar, id = "navbar_div"),

        # Page Content -- Div that contains page layout
        html.Div(id='page-content', style=CONTENT_STYLE),
    ]
)

@app.callback(
    [
        Output('page-content', 'children'),
        Output('sessionlogout', 'data'),
        Output('navbar_div', 'className'),
    ],
    [
        Input('index-url', 'pathname')
    ],
    [
        State('sessionlogout', 'data'),
        State('currentuserid', 'data'),
    ]
    
)
def displaypage (pathname, sessionlogout, userid):
    ctx = dash.callback_context
    if ctx.triggered:
        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        #print("Index page callback")
        #print("ctx.triggered: ", ctx.triggered)
        #print("User ID", userid)
        if eventid == 'index-url':
            if userid < 0:
                if pathname == '/':
                    #print("load login layout")
                    returnlayout = login.layout
                else:
                    returnlayout = '404: request not found'
            else:
                if pathname == '/logout':
                    returnlayout = login.layout
                    userid = -1
                    sessionlogout = True
                elif pathname == '/' or pathname == '/home':
                    returnlayout = home.layout
                elif pathname == '/accounts':
                    returnlayout = accounts.layout
                elif pathname == '/transactions':
                    returnlayout = transactions.layout
                else:
                    returnlayout = 'error404'

            logout_conditions = [
                pathname in ['/', '/logout'] and userid == -1,
                userid == -1,
                not userid
            ]
            sessionlogout = any(logout_conditions)

            navbar_classname = 'd-none' if sessionlogout else ''
            return [returnlayout, sessionlogout, navbar_classname]
        else:
            raise PreventUpdate
    else:
        #print("Displaypage else")
        raise PreventUpdate
    

    
if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050', new=0, autoraise=True)
    app.run_server(debug=False)