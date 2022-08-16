import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import plotly.express as px

from scrap import *

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
	'width': '20vw',
	'background-color': '#f8f9fa',
	'float':'left',
	'display':'inline',
	'height': '100vh'
}

# the style arguments for the main content page.
CONTENT_STYLE = {
	'width':'80vw',
	# 'minHeight': '100vh',
	# 'overflowY':'scroll',
	'float':'left',
	'display':'inline'
}

TEXT_STYLE = {
	'textAlign': 'center',
	'color': '#191970'
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
			value=dropdown_categories[0],  # default value
			multi=True
		),
		html.Br(),
		html.Button(
			id='submit_button',
			n_clicks=0,
			children='Plot fund',
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

content_row = html.Div(
	[
		dcc.Graph(id='graph_timeseries', style={"height": "60vh"}),
		dcc.Graph(id='graph_bars', style={"height": "60vh"})
	], style={'overflowY':'scroll'}
)

content = html.Div(
	[
		html.H2('Index Funds', style=TEXT_STYLE),
		html.Hr(),
		content_row,
	],
	style=CONTENT_STYLE
)

app = dash.Dash(suppress_callback_exceptions=True,
				external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css", 
				"assets/style.css"])
app.layout = html.Div([sidebar, content], style={'width': '100vw', 'margin': 0})


@app.callback(
	Output('graph_timeseries', 'figure'),
	[Input('submit_button', 'n_clicks')],
	[State('dropdown', 'value')])
def update_graph_timeseries(n_clicks, dropdown_value):
	df = fund_download(dropdown_value['value'])

	x = df[df.columns[0]].values
	y = df[df.columns[1]].values

	fig = px.line(df, x=x, y = y)
	return fig

@app.callback(
	Output('graph_bars', 'figure'),
	[Input('submit_button', 'n_clicks')],
	[State('dropdown', 'value')])
def update_graph_timeseries(n_clicks, dropdown_value):
	df = fund_download(dropdown_value['value'])

	df_bars = df.groupby(df.Date.dt.year).mean().reset_index()

	x = df_bars[df_bars.columns[0]].values
	y = df_bars[df_bars.columns[1]].values

	fig = px.bar(df_bars, x=x, y = y)

	# fig.update_traces(texttemplate='%{text:.2f}', textposition='inside')

	fig.add_hline(y=df[df.columns[1]].mean(), line_dash="dot",
						annotation_text=f"Mean: {round(df[df.columns[1]].mean(), 2)}", 
						annotation_position="bottom left",
						annotation_font_size=12,
						annotation_font_color="black")
	return fig

if __name__ == '__main__':
	app.run_server(port='8085')