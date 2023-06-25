# Everything common on all webpages

from dash import html
import dash_bootstrap_components as dbc

navlink_style = {
    'color': '#fff',
    'margin-left': '1em',
    'margin-right': '1em',
}

navbar = dbc.Navbar(
    [
        html.A(
            dbc.Row(
                [
                    dbc.Col(dbc.NavbarBrand("SpendSense", 
                                    style={'margin-right': '2em',
                                           'margin-left': '2em', 'color': '#fff'}),),
                ],
                align="center",
                class_name="g-0",
            ),               
            href="/home",
            style = {"text-decoration": "none"},
        ),
        dbc.NavLink("Accounts", href="/accounts", style=navlink_style),
        dbc.NavLink("Transactions", href="/transactions", style=navlink_style),
        dbc.NavLink("Logout", href="/logout", style=navlink_style),
    ],
    #dark=True,
    color='#3459e6',
)