from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import selenium.webdriver.support.ui as ui
import time

import ipywidgets as widgets
from IPython.display import display, clear_output
from datetime import datetime
import os
import shutil

import pandas as pd

today = str(datetime.now().date())

DOWNLOAD_FOLDER = f'./files/{today}/'
CHROMEDRIVER_URL = "c:\\chromedriver.exe"
WINDOW_SIZE = "1920,1080"


# Remove all obsolete folders
def remove_folders():
    for folder in os.listdir('./files'):
        if today not in folder:
            shutil.rmtree('./files/' + folder)


# Check if data has been downloaded
def check_if_downloaded(fund_name):
    if not os.path.exists(DOWNLOAD_FOLDER):
        remove_folders()
        os.makedirs(DOWNLOAD_FOLDER)
        
    l = [x for x in os.listdir(DOWNLOAD_FOLDER) if fund_name in x]
    
    if len(l) > 0:
        return True
    else:
        return False
    

# Load and return as a dataframe
def load_fund_df(fund_name):        
    l = [x for x in os.listdir(DOWNLOAD_FOLDER) if fund_name in x]
    df = pd.read_excel(DOWNLOAD_FOLDER + '/' + l[0], skiprows = 8, error_bad_lines=False)
    return df


def get_fund_list():
    funds_list = {}
    with open('./funds.txt', 'r') as file:
        for line in file:
            name, link = line.split('#')
            funds_list[name] = link
    return funds_list


# Download or retrieve data and display
def fund_download(new_fund):
    if type(new_fund) == list:
        new_fund = new_fund[0]

    funds_list = get_fund_list()
    link = funds_list[new_fund]

    if not check_if_downloaded(new_fund):
        print('Downloading...')
        scrap_fund(new_fund, link)

    print('Plotting dataframe...')
    df = load_fund_df(new_fund)
    df = clean_df(df)
    
    return df


# Scrap and download fund
def scrap_fund(fund_name, link):
    CHROMEDRIVER_URL = "c:\chromedriver.exe"
    WINDOW_SIZE = "1920,1080"
    DOWNLOAD_URL = f'C:\\Users\\Weronika\\Desktop\\Intrinsic_Value\\Vanguard\\files\\{today}\\'

    while True:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_URL,
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
            print("No cookies popup detected")
            print ('-------- RETRY --------')
            continue

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
    

# Clean dataframe
def clean_df(df):
    df['Date'] = pd.to_datetime(df['Date'])
    df[df.columns[1]] = df[df.columns[1]].str.replace('£', '')
    df[df.columns[1]] = df[df.columns[1]].str.replace('CHF', '')
    df[df.columns[1]] = df[df.columns[1]].str.replace('€', '')
    df[df.columns[1]] = df[df.columns[1]].str.replace('$', '')
    df[df.columns[1]] = df[df.columns[1]].str.replace('A', '')
    df[df.columns[1]] = df[df.columns[1]].astype(float)
    return df