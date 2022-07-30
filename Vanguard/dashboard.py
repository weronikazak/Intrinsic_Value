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
from data import Data
from lineplot import Line_Plot



class Dashboard():
	def __init__(self):
		self.data = Data()
		# self.graph_type = "line_plot"

		self.navbar = html.Div(["This is supposed to be a navbar."])
		self.main_graph = html.Div(["This is supposed to be a dashboard"])

		self.app = dash.Dash(__name__,
			suppress_callback_exceptions=True,
			external_stylesheets=["assets/bWLwgP.css", "assets/style.css"])


		self.main_plot = Line_Plot(self.app, self.data.df, self.data.funds)
		
		funds = []
		for fund in fund_list:
			funds.append({"label":fund, "value":fund})

		self.handle_layout()



	####### LAYOUT APPEARANCE #######
	def handle_layout(self):
		self.app.layout = html.Div([

			##### graph #####
			html.Div(
				style={
					"width":'85vw',
					'background':'red',
					'display':'inline-block'
				},
				id="graph-layout")
			],
			
			style={
				"display":"flex",
				"width":"100vw",
				'margin':0,
				'height':'100vh',
				'overflow':'hidden'}
		)


if __name__ == '__main__':
	dashboard = Dashboard()
	dashboard.app.run_server(debug=True)