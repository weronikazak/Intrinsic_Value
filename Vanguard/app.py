
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
	fund = list(get_fund_list().keys())[0]
	df = fund_download(fund)
	fund_to_plot = create_plot(df)
	return render_template('index.html', plot=fund_to_plot)


def create_plot(df):
	x = df[df.columns[0]].values
	y = df[df.columns[1]].values


	fund_data = go.Figure(data=go.Scatter(
						x=x, 
                        y=y,
                        marker_color='blue', 
						text="Index Price"))


	data = fund_data

	graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
	return graphJSON

if __name__ == '__main__':
	app.run()