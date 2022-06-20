import numpy as np
import pandas as pd
import os
import yfinance as yf
import datetime
import requests
from bs4 import BeautifulSoup as soup

current_year = datetime.datetime.now().year
current_month = datetime.datetime.now().month
years_forward = 4


def get_name(i):
	name = i["shortName"]
	return name


def get_current_price(i):
	current_price = i["currentPrice"]
	return current_price


def get_chart(h):
	chart_dates = h.index
	chart_values = h["Close"].values

	return chart_dates, chart_values


def get_details(tick):
	i = yf.Ticker(tick).info

	b = yf.Ticker(tick).balance_sheet
	b = b[b.columns[::-1]]
	b.columns = pd.DatetimeIndex(b.columns).year

	c = yf.Ticker(tick).cashflow
	c = c[c.columns[::-1]]
	c.columns = pd.DatetimeIndex(c.columns).year

	f = yf.Ticker(tick).financials
	f = f[f.columns[::-1]]
	f.columns = pd.DatetimeIndex(f.columns).year

	a = yf.Ticker(tick).analysis

	h = yf.Ticker(tick).history(period="5y")

	return i, b, c, f, a, h


def get_free_cashflow(c):
	CPO = c.loc["Total Cash From Operating Activities"].to_frame().T
	CAPEX = c.loc["Capital Expenditures"].to_frame().T
	FCF = (CPO.iloc[0] + CAPEX.iloc[0]).to_frame().T
	FCF.index = ["Free Cashflow"]
	FCF = CPO.append([CAPEX, FCF])
	return FCF


def get_net_income(c, FCF):
	net_income = c.loc["Net Income"].to_frame().T
	net_income.loc["Free Cash Flow to Equity"] = FCF.loc["Free Cashflow"]
	net_income.loc["FCFE/Net Income"] = (FCF.loc["Free Cashflow"] / net_income.loc["Net Income"])
	net_income.loc["FCFE/Net Income"] = net_income.loc["FCFE/Net Income"].round(2) * 100
	
	median_FFCE = net_income.loc["FCFE/Net Income"].median()
	
	return median_FFCE, net_income


def get_total_revenue(f, a):
	total_revenue = f.loc["Total Revenue"].to_frame().T
	total_revenue[current_year] = a["Revenue Estimate Low"].loc["0Y"]
	total_revenue[current_year+1] = a["Revenue Estimate Low"].loc["+1Y"]

	growths = [np.nan]
	for year1, year2 in zip(total_revenue, total_revenue.iloc[:, 1:]):
		y1 = total_revenue[year1].iloc[0]
		y2 = total_revenue[year2].iloc[0]
		growth = round((y2 - y1)/y1*100, 2)
		growths.append(growth)

	total_revenue.loc["Revenue Growth Rate"] = growths
	median_growth = total_revenue.loc["Revenue Growth Rate"].median()

	return median_growth, total_revenue

def get_net_income_margins(total_revenue, net_income):
	net_income_margins = pd.concat([total_revenue.loc["Total Revenue"].to_frame().T, net_income.loc["Net Income"].to_frame().T])
	
	net_income = []
	for year in net_income_margins.columns:
		revenue = net_income_margins[year].loc["Total Revenue"]
		netincome = net_income_margins[year].loc["Net Income"]
		net = round(netincome/revenue * 100, 2)
		net_income.append(net)
	net_income_margins.loc["Net Income Margins"] = net_income
	
	free_cashflow_rate_median = net_income_margins.loc["Net Income Margins"].median()

	return free_cashflow_rate_median, net_income_margins


def get_income_statement_ahead(net_income_margins, median_growth, median_FFCE, FCF, free_cashflow_rate_median):
	income_statement_numbers = net_income_margins.copy()
	income_statement_numbers = net_income_margins.drop(index="Net Income Margins", axis=0)
	income_statement_numbers = income_statement_numbers.append(FCF.loc["Free Cashflow"])

	for y in range(current_year, current_year+years_forward):
		rev = income_statement_numbers[y-1].loc["Total Revenue"] * (1+ (median_growth/ 100))
		n = rev * free_cashflow_rate_median / 100
		fcf = n * median_FFCE / 100
		income_statement_numbers[y] = [rev, n, fcf]
		
	return income_statement_numbers


def scrap_Rf():
	if (os.path.isfile('./TNX.txt')):
		with open("./TNX.txt", "r") as f:
			file_date = f.readline().strip()
			Rf = float(f.readline().strip())
			if file_date == f"{current_month}/{current_year}":
				return Rf

	page = requests.get("https://finance.yahoo.com/bonds")
	content = soup(page.content, "html.parser")
	Rf = float(content.find("fin-streamer", {"data-symbol":"^TNX"}).text)
	if Rf:
		with open("./TNX.txt", "w") as f:
			f.write(f"{current_month}/{current_year}\n{Rf}")
	else: 
		Rf = 3
	return Rf


def get_WACC(f, b, i):
	t = f[current_year-1].loc["Income Tax Expense"]/f[current_year-1].loc["Income Before Tax"]
	t = round(t, 4)

	rd = (round(abs(f[current_year-1].loc["Interest Expense"])*100 / 
			 (b[current_year-1].loc["Short Long Term Debt"]+b[current_year-1].loc["Long Term Debt"]),2))

	Rf = scrap_Rf()

	B = i["beta"] if i["beta"] else 0.8

	Rm = 10

	print(t, rd, Rf, B)

	Ra = Rf + B*(Rm - Rf)
	re = Ra

	total = i["totalDebt"] + i["marketCap"]
	wd = i["totalDebt"]*100/total
	we = i["marketCap"]*100/total

	WACC = round((wd*rd*(1-t) + we*re)/100,2)
	required_return = WACC
	r = required_return/100

	return r

def get_terminal_value(i, income_statement_numbers, r):
	perpetual_growth = 2.5
	g = perpetual_growth / 100

	FCFE0 = income_statement_numbers[current_year+years_forward-1].loc["Free Cashflow"]
	terminal_value = (FCFE0*(1+g))/(r-g)
	terminal_value = round(terminal_value)

	return terminal_value, g


def get_discount_factors(income_statement_numbers, r):
	cols_to_drop = list(filter(lambda x: x < current_year, income_statement_numbers.columns))
	discount_factors = income_statement_numbers.loc["Free Cashflow"].to_frame().T.drop(cols_to_drop, axis=1)

	discount_facs = []
	discount_val = []
	for (j, year) in enumerate(discount_factors.columns):
		discount = (1 + r)**(j+1)
		cashflow = discount_factors[year].loc["Free Cashflow"]
		discount_facs.append(discount)
		discount_val.append(cashflow/discount)
		
	discount_factors.loc["Discount Factor"] = discount_facs
	discount_factors.loc["PV of Future Cash Flow"] = discount_val
	return discount_factors

def get_intrinsic_value(i, terminal_value, discount_facs, margin_of_safety = 0.2):
	shares_outstanding = i["sharesOutstanding"]
	PV_of_terminal_value = round(terminal_value * discount_factors[current_year+years_forward-1].loc["Discount Factor"])
	todays_value = round(discount_factors.loc["PV of Future Cash Flow"].sum() + PV_of_terminal_value)
	
	fair_value_of_equity = todays_value/shares_outstanding
	intrinsic_value = fair_value_of_equity*(1-margin_of_safety)

	return intrinsic_value