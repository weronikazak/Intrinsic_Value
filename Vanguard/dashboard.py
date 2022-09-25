import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import plotly.express as px

from scrap import *

import numpy as np
import itertools

PLOTTED_DF = {}
TEST_MODE = False

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
	"position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
	'width': '20vw',
	'background-color': '#f8f9fa',
	'float':'left',
	'overflowY':'scroll'
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


GRAPH_STYLE = {
	'display':'block'
}

dropdown_categories = [{'label': val, 'value': val} for val in list(get_fund_list().keys())]

controls = html.Div(
	[
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
	], style={
		'padding':'0 10px'
	}
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
		html.Div(id='table', style={'margin':'0 5vw'}),
		dcc.Graph(id='graph_time_multi', style=GRAPH_STYLE),
		dcc.Graph(id='graph_bars', style=GRAPH_STYLE),
		dcc.Graph(id='graph_bars_month', style=GRAPH_STYLE),
		dcc.Graph(id='graph_corr', style=GRAPH_STYLE),
	],
	style=CONTENT_STYLE
)

app = dash.Dash(suppress_callback_exceptions=True,
				external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css", 
				"assets/style.css"])
app.layout = html.Div([sidebar, content])

def update_line_graph_timeseries(dropdown_value):
	fig = 0

	if len(list(dropdown_value)) == 1:
		if val not in PLOTTED_DF.keys():
			df = fund_download(dropdown_value, TEST_MODE)
			df.columns = ['Date', val]
			PLOTTED_DF[val] = df
		else:
			df = PLOTTED_DF[dropdown_value]

		x = df[df.columns[0]].values
		y = df[df.columns[1]].values

		fig = px.line(df, x=x, y = y, height=600)	
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
			if val not in PLOTTED_DF.keys():
				df = fund_download(val, TEST_MODE)
				df.columns = ['Date', val]
				PLOTTED_DF[val] = df
			else:
				df = PLOTTED_DF[val]
			data = pd.merge(data, df, how='outer', on='Date')

		fig = px.line(data, x='Date', y = data.columns, height=600)
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
			),
			ticklabelstep=12, dtick="M1", 
			tickformat="%Y", showticklabels=True
		)

	return fig

def update_area_graph_timeseries(dropdown_value):
	data = pd.DataFrame(columns=['Date'])

	for val in dropdown_value:
		if val not in PLOTTED_DF.keys():
			df = fund_download(val, TEST_MODE)
			df.columns = ['Date', val]
			PLOTTED_DF[val] = df
		else:
			df = PLOTTED_DF[val]
		data = pd.merge(data, df, how='outer', on='Date')

	data = calculate_rsi(data)
	data.columns.name = 'funds'
	data = data.set_index('Date')

	fig = px.line(data, facet_col='funds', facet_col_wrap=2, 
				height=int((len(data.columns)-1)/2)*500)
				
	fig.add_hline(y=20, line_dash="dot")
	fig.add_hline(y=60, line_dash="dot")

	# fig.update_yaxes(showticklabels=True, matches=None)
	fig.for_each_xaxis(lambda t: t.update(fixedrange=True))
	fig.for_each_yaxis(lambda t: t.update(fixedrange=True))
	# fig.update_xaxes(ticklabelstep=12, dtick="M1", 
	# 				tickformat="%Y",
	# 				matches=None, showticklabels=True)
	
	fig.update_layout(showlegend=False)

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
	[Output('graph_timeseries', 'figure'),
	Output('graph_time_multi', 'figure'),
	Output('graph_bars', 'figure'),
	Output('graph_corr', 'figure'),
	Output('table', 'children'),
	Output('graph_bars_month', 'figure')],
	[Input('submit_button', 'n_clicks'),
	Input('dropdown', 'value')])
def update_graphs(n_click, dropdown_value):
	if not dropdown_value:
		raise PreventUpdate

	f1 = update_line_graph_timeseries(dropdown_value)
	f2 = update_area_graph_timeseries(dropdown_value)
	f3 = update_bar_graph_timeseries(dropdown_value)
	f4 = update_corr_graph(dropdown_value)
	f5 = generate_table(dropdown_value)
	f6 = update_bar_graph_months(dropdown_value)


	return f1, f2, f3, f4, f5, f6

def generate_table(dropdown_value):
	data = pd.DataFrame(columns=['Date'])
	
	for val in dropdown_value:
		if val not in PLOTTED_DF.keys():
			df = fund_download(val, TEST_MODE)
			df.columns = ['Date', val]
			PLOTTED_DF[val] = df
		else:
			df = PLOTTED_DF[val]
		data = pd.merge(data, df, how='outer', on='Date')

	dd = pd.DataFrame(columns=['Current price', 
				'Profit (compared to yesterday)', 
				'Profit (compared to last month)',
				'Profit (compared to last 6 months)',
				'Profit (compared to last year)',
				'Profit (compared to last 5 years)',
				'Profit (compared to last 10 years)'],
			index=data.columns[1:])

	for fund in data.columns[1:]:
		try:
			p_today = data[fund].iloc[0]
			dd.loc[fund, 'Current price'] = p_today

			p_yesterday = data[fund].iloc[1]
			dd.loc[fund, 'Profit (compared to yesterday)'] = round(100*(p_today-p_yesterday)/p_yesterday, 2)

			p_month = data[fund].iloc[5*4]
			dd.loc[fund, 'Profit (compared to last month)'] = round(100*(p_today - p_month)/p_month, 2)

			p_6m = data[fund].iloc[5*4*6]
			dd.loc[fund, 'Profit (compared to last 6 months)'] = round(100*(p_today - p_6m)/p_6m, 2)

			p_year = data[fund].iloc[5*4*12]
			dd.loc[fund, 'Profit (compared to last year)'] = round(100*(p_today - p_year)/p_year, 2)

			p_5y =  data[fund].iloc[5*4*12*5]
			dd.loc[fund, 'Profit (compared to last 5 years)'] = round(100*(p_today - p_5y)/p_5y, 2)

			p_10y =  data[fund].iloc[5*4*12*10]
			dd.loc[fund, 'Profit (compared to last 10 years)'] = round(100*(p_today - p_10y)/p_10y, 2)
		except Exception as e:
			print(e)

	dd = dd.reset_index()

	RED = {'color': 'red'}
	GREEN = {'color': 'green'}
	BOLD = {'fontWeight': 'bold'}
	CURRENT_PRICE = {'background': '#eeeee4'}
	
	cols = []

	for i in range(len(dd)):
		trs = []
		for col in dd.columns:
			val = dd.iloc[i][col]
			try:
				if col == 'Current price':
					trs.append(html.Td(val, style=CURRENT_PRICE))
				elif float(val) < 0:
					trs.append(html.Td(str(val)+'%', style=RED))
				else:
					val = str(val) +'%' if val > 0 else '-'
					trs.append(html.Td(str(val), style=GREEN))
			except:
				trs.append(html.Td(val, style=BOLD))
		cols.append(html.Tr(trs))

	return html.Table([
		html.Thead(
			html.Tr([html.Th(val) for val in dd.columns])
		),
		html.Tbody(cols)
	])

def update_bar_graph_timeseries(dropdown_value):
	data = pd.DataFrame(columns=['Date'])
	for val in dropdown_value:
		if val not in PLOTTED_DF.keys():
			df = fund_download(val, TEST_MODE)
			df.columns = ['Date', val]
			PLOTTED_DF[val] = df
		else:
			df = PLOTTED_DF[val]

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
	
	df_bars_m['color'] = 'blue'
	df_bars_m.loc[df_bars_m['value'] < 0, 'color'] = 'red'

	num_rows = int(len(df_bars.columns)/2)

	fig = px.bar(df_bars_m, x="Date", y="value", facet_col="variable", facet_col_wrap=2,
				color='color', text_auto=True, height=num_rows*500, facet_col_spacing = 0.075)
	
	rows = list(reversed(range(1, num_rows+1)))
	row_col = list(itertools.product(rows, [1, 2]))

	for ticker, idx in zip(df_bars.columns[1:], row_col):
		means = df_bars[ticker].mean()

		fig.add_hline(y=means, line_dash="dot",
						annotation_text=f"Mean: {round(means, 2)}", 
						annotation_position="top left",
						annotation_font_size=12,
						annotation_font_color="black",
						row=idx[0], col=idx[1])

	fig.update_yaxes(
					# matches=None, 
					showticklabels=True)
	fig.update_xaxes(ticklabelstep=1, dtick="M1", 
					tickformat="%b\n%Y",
					matches=None, showticklabels=True)
	
	fig.update_traces(textfont_size=12, 
						textangle=0, 
						textposition="outside", 
						cliponaxis=False)
	
	return fig


def update_bar_graph_months(dropdown_value):
	data = pd.DataFrame(columns=['Date'])
	for val in dropdown_value:
		if val not in PLOTTED_DF.keys():
			df = fund_download(val, TEST_MODE)
			df.columns = ['Date', val]
			PLOTTED_DF[val] = df
		else:
			df = PLOTTED_DF[val]

		data = pd.merge(data, df, how='outer', on='Date')

	current_year = datetime.now().year
	data['year-month'] = data.Date.dt.strftime('%Y-%m')
	data = data[((data.Date.dt.year == current_year) | (data['year-month'] == f'{current_year-1}-12'))].groupby('year-month').mean()

	df_bars = pd.DataFrame()
	for prev, nxt in zip(data.iterrows(), data.iloc[1:, :].iterrows()):
		i, row_prev = prev
		j, row_next = nxt
		
		increase = round(100*(row_prev - row_next)/row_prev, 2)
		increase.name = j
		df_bars = df_bars.append(increase)

	df_bars = df_bars.reset_index()
	df_bars_m = df_bars.melt(id_vars=['index']).dropna()
	
	df_bars_m['color'] = 'blue'
	df_bars_m.loc[df_bars_m['value'] < 0, 'color'] = 'red'

	num_rows = int(len(df_bars.columns)/2)

	fig = px.bar(df_bars_m, x="index", y="value", facet_col="variable", facet_col_wrap=2,
				color='color', text_auto=True, height=num_rows*500, facet_col_spacing = 0.075)
	
	rows = list(reversed(range(1, num_rows+1)))
	row_col = list(itertools.product(rows, [1, 2]))

	for ticker, idx in zip(df_bars.columns[1:], row_col):
		means = df_bars[ticker].mean()

		fig.add_hline(y=means, line_dash="dot",
						annotation_text=f"Mean: {round(means, 2)}", 
						annotation_position="top left",
						annotation_font_size=12,
						annotation_font_color="black",
						row=idx[0], col=idx[1])

	fig.update_yaxes(
					# matches=None, 
					showticklabels=True)
	fig.update_xaxes(ticklabelstep=1, dtick="M1", 
					tickformat="%b\n%Y",
					matches=None, showticklabels=True)
	
	fig.update_traces(textfont_size=12, 
						textangle=0, 
						textposition="outside", 
						cliponaxis=False)
	
	return fig


def update_corr_graph(dropdown_value):
	data = pd.DataFrame(columns=['Date'])
	for val in dropdown_value:
		if val not in PLOTTED_DF.keys():
			df = fund_download(val, TEST_MODE)
			df.columns = ['Date', val]
			PLOTTED_DF[val] = df
		else:
			df = PLOTTED_DF[val]
		data = pd.merge(data, df, how='outer', on='Date')

	df_bars = data.groupby(data.Date.dt.year).mean().reset_index()

	for future, past in zip(df_bars.iloc[1:].iterrows(), df_bars.iterrows()):
		i, row_f = future
		j, row_p = past
		for col in df_bars.columns[1:]:
			profit = round(100*(row_f[col] - row_p[col])/ row_p[col], 2)
			df_bars.loc[j, col] = profit
	df_bars = df_bars.iloc[:-1]
	num_rows = len(df_bars.columns)
	fig = px.imshow(df_bars.iloc[:, 1:].corr(), text_auto=True, aspect="auto",
					height=num_rows*80)
	fig.update_xaxes(side="top")
	# fig.update_layout(showlegend=False)
	return fig


if __name__ == '__main__':
	app.run_server(port='8085')