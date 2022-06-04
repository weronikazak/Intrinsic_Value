import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as soup
import requests
from datetime import date
import yfinance as yf


def get_by_tick(tick):
    df = pd.read_csv("companies.csv")
    row = df[(df == tick).any(axis=1)]
    return row.values[0]


def get_page_content(link):
    page = requests.get(link, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'})
    content = soup(page.content, "html.parser")
    return content


def get_current_cashflow(ticker, last_year=3000):
    URL = f"https://www.macrotrends.net/stocks/charts/{ticker}/whatever/free-cash-flow"
    page = get_page_content(URL)
    cashflows = {}

    tbody = page.find("table", "historical_data_table").find("tbody")
    for tr in reversed(tbody.findAll("tr")):
        trs = tr.findAll("td")
        year = int(trs[0].text.split("-")[0])
        if year > last_year or year == date.today().year: continue # eliminate post-covid
        price = float(trs[1].text.replace(",","").strip())
        cashflows[year] = price
    return cashflows


def get_growth_rates(cashflows):
    df = pd.DataFrame([cashflows])
    growth_rates = {}

    for year1, year2 in zip(df, df.iloc[:, 1:]):
        price1 = df[year1].iloc[0]
        price2 = df[year2].iloc[0]
        growth_rate = (price2 - price1) / price1
        growth_rates[year2] = round(growth_rate, 4)
    avg_growth_rate = round(np.mean(list(growth_rates.values())), 4)
    return growth_rates, avg_growth_rate


def get_future_cashflows(cashflows, years, avg_growth_rate):
    future_cashflows = {}
    year = date.today().year + 1
    future_cashflows[year] = np.floor(cashflows[list(cashflows.keys())[-1]] * (1 + avg_growth_rate))
    for year in range(year + 1, year + years):
        future_cashflows[year] = np.floor(future_cashflows[year-1] + (future_cashflows[year-1] * avg_growth_rate))

    return future_cashflows


def get_terminal_value(future_cashflows, perpetual_growth_rate, dicount_rate):
    price_last = future_cashflows[list(future_cashflows.keys())[-1]]
    terminal_value = np.floor(price_last * (1+perpetual_growth_rate) / (dicount_rate-perpetual_growth_rate))
    future_cashflows["Terminal"] = terminal_value
    return future_cashflows


def get_PV_of_FFCFs(future_cashflows, dicount_rate):
    PV_of_FFCFs = {}
    for (i, key) in enumerate(future_cashflows.keys()):
        PV_of_FFCFs[key] = np.floor(future_cashflows[key] / (1 + dicount_rate)**(i+1))
    sum_of_FFCFs = np.sum(list(PV_of_FFCFs.values()))
    return PV_of_FFCFs, sum_of_FFCFs


def get_cash_and_eq(tick):
    return yf.Ticker(tick).balance_sheet.loc["Cash"][0]/1_000_000


def get_total_debt_and_shares(tick):
    total_debt = int(yf.Ticker(tick).info["totalDebt"]/1_000_000)
    shares_outstanding = int(yf.Ticker(tick).info['sharesOutstanding']/1_000_000)

    return total_debt, shares_outstanding


def get_equity_and_intrinsic(sum_of_FCF, cash_and_eq, total_debt, shares_outstanding):
    equity_value = sum_of_FCF + cash_and_eq - total_debt
    
    price_per_share = round(equity_value / shares_outstanding, 2)
    
    return equity_value, price_per_share