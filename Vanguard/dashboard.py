import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import plotly.express as px

from scrap import *

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


GRAPH_STYLE = {
	'height': 600,
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

content = html.Div(
	children=[
		html.H2('Index Funds', style=TEXT_STYLE),
		html.Hr(),
		dcc.Graph(id='graph_timeseries', style=GRAPH_STYLE),
		dcc.Graph(id='graph_bars', style=GRAPH_STYLE),
	],
	style=CONTENT_STYLE
)

app = dash.Dash(suppress_callback_exceptions=True,
				external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css", 
				"assets/style.css"])
app.layout = html.Div([sidebar, content])


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