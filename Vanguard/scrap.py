import numpy as np
import os
import pandas as pd
import requests
import datetime
import requests
from bs4 import BeautifulSoup as soup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import selenium.webdriver.support.ui as ui
import time

CHROMEDRIVER_URL = "c:\chromedriver.exe"
WINDOW_SIZE = "1920,1080"

def get_funds():
	URL = "https://www.vanguardinvestor.co.uk/what-we-offer/all-products"

	chrome_options = Options()
	chrome_options.add_argument("--headless")
	chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)

	driver = webdriver.Chrome(executable_path=CHROMEDRIVER_URL, options=chrome_options)
	driver.implicitly_wait(5)
	driver.get(URL)

	funds = {}

	names = driver.find_elements(By.XPATH, "//h2[contains(@class, 'mr-3')]")
	charges = driver.find_elements(By.XPATH, "//div[contains(@class, 'fund-card__text-bold') and contains(text(),'%')]")
	for i, name in enumerate(names):
	    funds[name.text] = charges[i].text

	driver.close()

	return funds


def get_fund_links(funds):
	URL = 'https://www.vanguard.co.uk/professional/product'

	chrome_options = Options()
	chrome_options.add_argument("--headless")
	chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)

	driver = webdriver.Chrome(executable_path=CHROMEDRIVER_URL, options=chrome_options)
	driver.implicitly_wait(5)
	driver.get(URL)

	fund_links = {}

	for i, fund_name in enumerate(funds.keys()):
	    f = driver.find_element(By.XPATH, f"//a[contains(text(), '{fund_name}')]")
	    fund_links[fund_name] = f.get_attribute("href")
	    print(i, f.get_attribute("href"))

	driver.close()

	return fund_links

def scrap_funds(fund_links):
	for link in list(fund_links.values()):
	    chrome_options = Options()
	    chrome_options.add_argument("--headless")
	    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
	    chrome_options.add_experimental_option("prefs", {
	            "download.default_directory": r'C:\Users\Weronika\Desktop\Intrinsic_Value\Vanguard\files\\',
	            "download.prompt_for_download": False,
	            "download.directory_upgrade": True,
	            "safebrowsing_for_trusted_sources_enabled": False,
	            "safebrowsing.enabled": False
	    })

	    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_URL, options=chrome_options)
	    driver.implicitly_wait(15)
	    driver.get(link)
	    wait = ui.WebDriverWait(driver,15)
	    
	    try:
	        driver.find_element(By.ID, "onetrust-reject-all-handler").click()
	        wait.until(lambda driver: driver.find_element(By.XPATH, "//button[contains(text(), 'I agree')]"))
	        driver.find_element(By.XPATH, "//button[contains(text(), 'I agree')]").click()
	        driver.implicitly_wait(10)
	    except Exception as e:
	        print(e)
	        print(link)
	        print("No cookies popup detected")
	        driver.close() 
	        break
	    wait.until(lambda driver: driver.find_element(By.XPATH, "//span[contains(text(), 'Download') and contains(text(), 'prices')]"))
	    driver.find_element(By.XPATH, "//span[contains(text(), 'Download') and contains(text(), 'prices')]").click()
	    time.sleep(5)
	    driver.close()


if __name__ == '__main__':
	funds = get_funds()
	fund_links = get_fund_links(funds)
	scrap_funds(fund_links)