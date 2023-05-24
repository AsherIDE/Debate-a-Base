# # import dash
# # import dash_core_components as dcc
# # import dash_html_components as html
# # import plotly.express as px
# # import pandas as pd
# from dash import Dash, html, callback, dcc, Input, Output

# # assume you have a "long-form" data frame
# # see https://plotly.com/python/px-arguments/ for more options
# # df = pd.DataFrame(
# #     {
# #         "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
# #         "Amount": [4, 1, 2, 2, 4, 5],
# #         "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"],
# #     }
# # )

# def make_dash(server):
#     return Dash(
#         server=server,
#         url_base_pathname='/dash/'
#     )

# def make_layout():
#     return html.Div(                                                                                                                                                                                                 
#         [                                                                                                                                                                                                            
#             html.P("Hey this is a Dash app :)"),                                                                                                                                                                     
#             dcc.Input(id="input"),                                                                                                                                                                                   
#             html.Div(id="output"),                                                                                                                                                                                   
#         ]                                                                                                                                                                                                            
#     )

# def define_callbacks():
#     @callback(
#         Output("output", "children"),
#         Input("input", "value"),
#     )
#     def show_output(text):
#         return f"you entered: '{text}'"


# # def create_dash_application(flask_app, df):
# #     dash_app = dash.Dash(server=flask_app, name="Dashboard", url_base_pathname="/")
# #     dash_app.layout = html.Div(
# #         children=[
# #         #     html.H1(children="xddd"),
# #         #     html.Div(
# #         #         children="""
# #         #     Dash: A web application framework for Python.
# #         # """
# #         #     ),
# #             dcc.Graph(
# #                 id="ngram",
# #                 figure=px.bar(df, x="Fruit", y="Amount", color="City", barmode="group"),
# #             ),
# #         ]
# #     )

# #     return dash_app