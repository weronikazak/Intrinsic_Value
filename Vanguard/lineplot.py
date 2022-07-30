import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash_table
import re
import os
import pandas as pd
import requests
from dash.dependencies  import Input, Output, State
import plotly.graph_objs as go
import datetime


class Line_Plot():
	def __init__(self, app, data, fund_list):
		self.data = data
		funds = []
		for fund in fund_list:
			funds.append({"label":fund, "value":fund})
		print(funds)

		self.graph = html.Div([dcc.Graph(id="graph-line")],
			style={
				"width":'85vw',
				'display':'inline-block'
			})

		app.callback(
			Output("graph-line", "figure"),
			[Input("funds-line", "value"),
			Input("date-line", "value")])(self.update_funds_plot)


		self.navbar = html.Div([

			##### FUNDS #####
			html.Label("Funds"),
			dcc.Dropdown(
				id="funds-line",
				options = funds,
				value=fund_list[0],
				multi=True),


			##### TIMELINE #####
			html.Label("Date"),
			dcc.Slider(
				id="date-line",
				min=0,
				max=10),
				]
			)


	def update_funds_plot(self, funds, date):
		df = self.data
		print(df)
		columns = df.columns

		fig = px.line(df, x=columns[0], y=columns[1])

		# # fig.update_layout(margin={'l': 40, 'b': 10, 't': 10, 'r': 40},
		# # 	hovermode='closest', showlegend=False)
		fig.update_layout(legend=dict(
			orientation="h",
			yanchor="top",
			xanchor="center",
			y=-0.3,
			x=0.5))

		# fig.update_xaxes(type=radio)
		# fig.update_yaxes(type=radio)

		print('It shuld plot :D')
		return 