
from flask import Flask, render_template, url_for, redirect, Response, request
from utils import *
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def index():
 return redirect(url_for('stock_profile', tick='AAPL'))


@app.route('/<tick>')
def stock_profile(tick):
	if (len(tick) > 5):
		tick ="AAPL"

	perpetual_growth_rate = 0.01
	dicount_rate = 0.1
	years_holding = 7
	year_range = 2023

	if request.method == "POST":
	   perpetual_growth_rate = request.form.get("growthRate")
	   dicount_rate = request.form.get("dicountRate")
	   years_holding = request.form.get("yearsHolding")

	ticker_class = yf.Ticker(tick)
	name = ticker_class.info["shortName"]
	current_price = ticker_class.info["currentPrice"]
	cash_and_eq = ticker_class.balance_sheet.loc["Cash"][0]/1_000_000
	total_debt = int(ticker_class.info["totalDebt"]/1_000_000)
	shares_outstanding = int(ticker_class.info['sharesOutstanding']/1_000_000)

	chart_his = ticker_class.history(period="5y")
	chart_dates = chart_his.index
	chart_values = chart_his["Close"].values

	cashflows = get_current_cashflow(tick, year_range)
	growth_rates, avg_growth_rate = get_growth_rates(cashflows)
	future_cashflows = get_future_cashflows(cashflows, years_holding, avg_growth_rate)
	future_cashflows = get_terminal_value(future_cashflows, perpetual_growth_rate, dicount_rate)
	PV_of_FFCFs, sum_of_FCFs = get_PV_of_FFCFs(future_cashflows, dicount_rate)
	equity_value, price_per_share = get_equity_and_intrinsic(sum_of_FCFs, cash_and_eq, total_debt, shares_outstanding)

	values = {
		"ticker": tick,
		"name": name,
		"cashflows": cashflows,
		"growth_rates": growth_rates,
		"avg_growth_rate": avg_growth_rate,
		"future_cashflows": future_cashflows,
		"PV_of_FFCFs": PV_of_FFCFs,
		"sum_of_FCFs": sum_of_FCFs,
		"cash_and_eq": cash_and_eq,
		"total_debt" : total_debt,
		"shares_outstanding": shares_outstanding,
		"equity_value" : equity_value,
		"price_per_share": price_per_share,
		"current_price_per_share": current_price,
		"chart_dates": chart_dates,
		"chart_values":chart_values

	}
	return render_template('index.html', val=values)
