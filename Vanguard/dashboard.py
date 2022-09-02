import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import plotly.express as px

from scrap import *

import numpy as np
import itertools

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
	"position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
	'width': '20vw',
	'background-color': '#f8f9fa',
	'float':'left',
}

# the style arguments for the main content page.
CONTENT_STYLE = {
	"position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
	'width':'80vw',
	'float':'left',
	"display": "inline-block",
	'marginLeft':'20vw',
	'overflowY':'scroll'
}

TEXT_STYLE = {
	'textAlign': 'center',
	'color': '#191970'
}


GRAPH_STYLE_1 = {
	'height': 600,
	'display':'block'
}

GRAPH_STYLE_2 = {
	'height': int(),
	'display':'block'
}

dropdown_categories = [{'label': val, 'value': val} for val in list(get_fund_list().keys())]

controls = html.Div(
	[
		html.P('Dropdown', style={
			'textAlign': 'center'
		}),
		dcc.Dropdown(
			id='dropdown',
			options=dropdown_categories,
			value=[dropdown_categories[0]['value']],  # default value
			multi=True
		),
		html.Br(),
		html.Button(
			id='submit_button',
			n_clicks=0,
			children='Plot fund',
		),
		html.Br(),
		html.Button(
			id='my_funds_button',
			n_clicks=0,
			children='My funds',
		),
	]
)

sidebar = html.Div(
	[
		html.H2('Choose Funds', style=TEXT_STYLE),
		html.Hr(),
		controls
	],
	style=SIDEBAR_STYLE,
)

content = html.Div(
	children=[
		html.H2('Index Funds', style=TEXT_STYLE),
		html.Hr(),
		dcc.Graph(id='graph_timeseries', style=GRAPH_STYLE),
		dcc.Graph(id='graph_time_multi', style=GRAPH_STYLE),
		dcc.Graph(id='graph_bars', style=GRAPH_STYLE),
	],
	style=CONTENT_STYLE
)

app = dash.Dash(suppress_callback_exceptions=True,
				external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css", 
				"assets/style.css"])
app.layout = html.Div([sidebar, content])

@app.callback(
    [Output('graph_time_multi', 'figure'), 
	Output('graph_bars', 'figure')],
    Input('dropdown', 'value')
)
def update_output(value):
    return f'You have selected {value}'

@app.callback(
	Output('graph_timeseries', 'figure'),
	[Input('submit_button', 'n_clicks'),
	Input('dropdown', 'value')])
def update_line_graph_timeseries(n_clicks, dropdown_value):
	if not dropdown_value:
		raise PreventUpdate
	fig = 0

	if len(list(dropdown_value)) == 1:
		df = fund_download(dropdown_value)

		x = df[df.columns[0]].values
		y = df[df.columns[1]].values

		fig = px.line(df, x=x, y = y)	
		fig.update_xaxes(
			rangeslider_visible=True,
			rangeselector=dict(
				buttons=list([
					dict(count=1, label="1m", step="month", stepmode="backward"),
					dict(count=6, label="6m", step="month", stepmode="backward"),
					dict(count=1, label="YTD", step="year", stepmode="todate"),
					dict(count=1, label="1y", step="year", stepmode="backward"),
					dict(step="all")
				])
			)
		)
	elif len(list(dropdown_value)) > 1:	
		data = pd.DataFrame(columns=['Date'])
		
		for val in dropdown_value:
			df = fund_download(val)
			df.columns = ['Date', val]
			data = pd.merge(data, df, how='outer', on='Date')

		fig = px.line(data, x='Date', y = data.columns)
		fig.update_xaxes(
			# rangeslider_visible=True,
			rangeselector=dict(
				buttons=list([
					dict(count=1, label="1m", step="month", stepmode="backward"),
					dict(count=6, label="6m", step="month", stepmode="backward"),
					dict(count=1, label="YTD", step="year", stepmode="todate"),
					dict(count=1, label="1y", step="year", stepmode="backward"),
					dict(count=5, label="5y", step="year", stepmode="backward"),
					dict(step="all")
				])
			)
		)
	return fig

@app.callback(
	Output('graph_time_multi', 'figure'),
	[Input('submit_button', 'n_clicks'),
	Input('dropdown', 'value')])
def update_area_graph_timeseries(n_clicks, dropdown_value):
	if not dropdown_value:
		raise PreventUpdate
	
	data = pd.DataFrame(columns=['Date'])

	for val in dropdown_value:

		df = fund_download(val)
		df.columns = ['Date', val]
		data = pd.merge(data, df, how='outer', on='Date')

	data.columns.name = 'funds'
	data = data.set_index('Date')
	fig = px.area(data, facet_col='funds', facet_col_wrap=2)

	return fig

@app.callback(
	Output('dropdown', 'value'),
	Input('my_funds_button', 'n_clicks'))
def update_dropdown(n_clicks):
	my_funds = [
		'S&P 500 UCITS ETF', 
		'U.S. Equity Index Fund',
		'FTSE Developed World ex-U.K. Equity Index Fund',
		'FTSE All-World UCITS ETF',
		'Global Bond Index Fund'
	]

	return my_funds 

@app.callback(
	Output('graph_bars', 'figure'),
	[Input('submit_button', 'n_clicks'),
	Input('dropdown', 'value')])
def update_bar_graph_timeseries(n_clicks, dropdown_value):
	if not dropdown_value:
		raise PreventUpdate
	
	data = pd.DataFrame(columns=['Date'])

	for val in dropdown_value:

		df = fund_download(val)
		df.columns = ['Date', val]

		data = pd.merge(data, df, how='outer', on='Date')

	df_bars = data.groupby(data.Date.dt.year).mean().reset_index()

	for future, past in zip(df_bars.iloc[1:].iterrows(), df_bars.iterrows()):
		i, row_f = future
		j, row_p = past
		for col in df_bars.columns[1:]:
			profit = round(100*(row_f[col] - row_p[col])/ row_p[col], 2)
			df_bars.loc[j, col] = profit
	df_bars = df_bars.iloc[:-1]
	df_bars_m = df_bars.melt(id_vars=['Date']).dropna()

	fig = px.bar(df_bars_m, x="Date", y="value", facet_col="variable", facet_col_wrap=2)
	
	for i, ticker in enumerate(df_bars.columns[1:]):
		means = df_bars[ticker].mean()
		row = col = 0
		if i > 0:
			row = int(i / 2)
			col = i % 2
		print(i, row, col, ticker, means)

		fig.add_hline(y=means, line_dash="dot", row=row, col=col,
						annotation_text=f"Mean: {round(means, 2)}", 
						annotation_position="bottom left",
						annotation_font_size=12,
						annotation_font_color="black")
	
	# fig.add_hline(y=120, line_dash="dot",
	# 					annotation_text=f"Mean: 120", 
	# 					annotation_position="bottom left",
	# 					annotation_font_size=16,
	# 					annotation_font_color="black")
	
	fig.update_xaxes(ticklabelstep=1, dtick="M1", tickformat="%b\n%Y")
	return fig

if __name__ == '__main__':
	app.run_server(port='8085')