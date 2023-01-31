from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import chromedriver_autoinstaller

import selenium.webdriver.support.ui as ui
import time

from IPython.display import display, clear_output
from datetime import datetime
import os
import shutil

import pandas as pd
import numpy as np
import shutil

from currency_converter import CurrencyConverter

today = str(datetime.now().date())

SAVE_TO=os.getcwd() + '\\files\\'
DOWNLOAD_FOLDER = SAVE_TO + today + '\\' 
TEST_FOLDER = SAVE_TO + 'test\\' 

FUNDS_LIST = os.getcwd() + '\\funds.txt'

DISK = 'C'

CHROME_VERSION = (chromedriver_autoinstaller.get_chrome_version()).split('.')[0]
CHROMEDRIVER_DIR = f"{DISK}:\{CHROME_VERSION}"
CHROMEDRIVER_URL = f"{DISK}:\chromedriver.exe"

WINDOW_SIZE = "1920,1080"

# Check whether Chrome up to date
def download_chrome_driver():
    chromedriver_autoinstaller.install(path=DISK + ':\\')
    if CHROME_VERSION is not "" and os.path.exists(CHROMEDRIVER_DIR):
        os.replace(CHROMEDRIVER_DIR + '\chromedriver.exe', CHROMEDRIVER_URL)
        os.rmdir(CHROMEDRIVER_DIR)

# Calculate RSI
def calculate_rsi(data, period=10):
    d = pd.DataFrame()
    d['Date'] = data['Date']

    for col in data.columns[1:]:
        c = data[col]
        c = c.replace({0:np.nan})
        c = c.dropna().reset_index(drop=True)

        net_change = c.diff()
        increase = net_change.clip(lower=0)
        decrease = -1*net_change.clip(upper=0)
        ema_up = increase.ewm(com=period, adjust=False).mean()
        ema_down = decrease.ewm(com=period, adjust=False).mean()
        RS = ema_up/ema_down
        d[f'RSI_{col}'] = 100 - (100/(1+RS)) 
    return d


# Remove all obsolete folders
def remove_folders():
    if not os.path.exists(SAVE_TO):
        os.makedirs(SAVE_TO)
    
    for folder in os.listdir(SAVE_TO):
        if today not in folder:
            shutil.rmtree(SAVE_TO + folder)


# Check if data has been downloaded
def check_if_downloaded(fund_name, testing):
    download_chrome_driver()

    URL = DOWNLOAD_FOLDER
    if testing:
        URL = TEST_FOLDER

    if not os.path.exists(URL) and not testing:
        remove_folders()
        os.makedirs(URL)
        
    l = [x for x in os.listdir(URL) if fund_name in x]
    
    if len(l) > 0:
        return True
    else:
        return False
    

# Load and return as a dataframe
def load_fund_df(fund_name, testing):
    URL = DOWNLOAD_FOLDER   
    if testing:
        URL = TEST_FOLDER
        
    l = [x for x in os.listdir(URL) if fund_name in x]
    print(URL + l[0])
    df = pd.read_excel(URL + l[0], skiprows = 8)
    return df


def get_fund_list():
    funds_list = {}
    with open(FUNDS_LIST, 'r') as file:
        for line in file:
            name, link = line.split('#')
            funds_list[name] = link
    return funds_list


# Download or retrieve data and display
def fund_download(new_fund, testing=False):
    if type(new_fund) == list:
        new_fund = new_fund[0]

    funds_list = get_fund_list()
    link = funds_list[new_fund]

    if not check_if_downloaded(new_fund, testing):
        print('Downloading...')
        scrap_fund(new_fund, link)

    print('Plotting dataframe...')
    df = load_fund_df(new_fund, testing)
    df = df.drop(df.iloc[:, 2:], axis=1)
    df = convert_currency(df)

    return df


# Scrap and download fund
def scrap_fund(fund_name, link):
    WINDOW_SIZE = "1920,1080"

    while True:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        # chrome_options.binary_location = 
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_FOLDER,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False,
            "excludeSwitches": ["enable-automation"],
            'useAutomationExtension': False,
            'Access-Control-Allow-Origin': '*'
        })

        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_URL, options=chrome_options)
        driver.implicitly_wait(15)
        driver.get(link)
        wait = ui.WebDriverWait(driver,15)

        try:
            driver.find_element(By.ID, "onetrust-reject-all-handler").click()
            wait.until(lambda driver: driver.find_element(By.XPATH, "//span[contains(text(), ' I agree')]"))
            driver.find_element(By.XPATH, "//button[contains(text(), ' I agree')]").click()
            driver.implicitly_wait(10)
        except Exception as e:
            print("No cookies popup detected")
            print ('-------- RETRY --------')
            continue

        try:
            wait.until(lambda driver: driver.find_element(By.XPATH, "//span[contains(text(), ' I agree')]"))
            driver.find_element(By.XPATH, "//span[contains(text(), ' I agree')]").click()
            driver.implicitly_wait(10)
        except Exception as e:
            print("No agreement popup detected")
            print ('-------- RETRY --------')
            # continues


        try:
            wait.until(lambda driver: driver.find_element(By.XPATH, "//span[contains(text(), 'Download') and contains(text(), 'prices')]"))
            driver.find_element(By.XPATH, "//span[contains(text(), 'Download') and contains(text(), 'prices')]").click()
        except Exception as e:
            print('Runtime when trying to spot the download button')
            print ('-------- RETRY --------')
            print (fund_name)
            continue

        time.sleep(5)
        driver.close()
        print(f'Fund {fund_name} downloaded.')
        return False


def convert_currency(df):
    c = CurrencyConverter()
    col = df.columns[1]

    df['Date'] = pd.to_datetime(df['Date'])
    
    if 'USD' in df[col].iloc[2] or 'US' in df[col].iloc[2]:
        df[col] = df[col].str.replace('$', '')
        df[col] = df[col].str.replace('US', '')
        df[col] = df[col].str.replace('USD', '')
        df[col] = df[col].astype(float)
        df[col] = df[col].apply(lambda x: round(c.convert(x, 'USD', 'GBP'), 2))

    elif 'CHF' in df[col].iloc[2]:
        df[col] = df[col].str.replace('CHF', '')
        df[col] = df[col].astype(float)
        df[col] = df[col].apply(lambda x: round(c.convert(x, 'CHF', 'GBP'), 2))
        
    elif 'A' in df[col].iloc[2] or 'AUD' in df[col].iloc[2]:
        df[col] = df[col].str.replace('A', '')
        df[col] = df[col].str.replace('AUD', '')
        df[col] = df[col].str.replace('$', '')
        df[col] = df[col].astype(float)
        df[col] = df[col].apply(lambda x: round(c.convert(x, 'AUD', 'GBP'), 2))

    elif '€' in df[col].iloc[2] or 'EUR' in df[col].iloc[2]:
        df[col] = df[col].str.replace('EUR', '')
        df[col] = df[col].str.replace('€', '')
        df[col] = df[col].astype(float)
        df[col] = df[col].apply(lambda x: round(c.convert(x, 'EUR', 'GBP'), 2))

    else:
        df[col] = df[col].str.replace('£', '')
        df[col] = df[col].str.replace('GBP', '')
        df[col] = df[col].astype(float)
    
    return df