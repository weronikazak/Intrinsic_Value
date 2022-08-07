
from flask import Flask, render_template, url_for, redirect, Response, request
from scrap import *
import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import json

app = Flask(__name__)

@app.route('/')
def index():
	fund_list = list(get_fund_list().keys())
	df = fund_download(fund_list[0])
	graph_line, graph_bar = create_plot(df)
	return render_template('index.html', plot_line=graph_line, plot_bar=graph_bar, fund_list=fund_list)


def create_plot(df):
	x = df[df.columns[0]].values
	y = df[df.columns[1]].values


	fund_data = go.Figure(data=go.Scatter(
						x=x, 
                        y=y,
                        marker_color='blue', 
						text="Index Price"))

	df_bars = df.groupby(df.Date.dt.year).mean().reset_index()

	bars_data = go.Figure(data=go.Bar(
						x=df_bars[df_bars.columns[0]].values, 
                        y=df_bars[df_bars.columns[1]].values,
                        marker_color='blue',
						text =df_bars.columns[1],
    					textposition='outside'))

	bars_data.update_xaxes(
						title_text = df_bars.columns[0],
						title_font = {"size": 20},
						title_standoff = 25)

	bars_data.add_hline(y=df[df.columns[1]].mean(), line_dash="dot",
						annotation_text=f"Mean: {round(df[df.columns[1]].mean(), 2)}", 
						annotation_position="bottom right",
						annotation_font_size=12,
						annotation_font_color="black")


	graph_line = json.dumps(fund_data, cls=plotly.utils.PlotlyJSONEncoder)
	graph_bar = json.dumps(bars_data, cls=plotly.utils.PlotlyJSONEncoder)
	return (graph_line, graph_bar)

if __name__ == '__main__':
	app.run()