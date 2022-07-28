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

####### SCRAPED DATA ########
class Data:
	def __init__(self):
		self.funds_list = {}
		self.funds = self.get_list_of_funds()

		self.today = str(datetime.now().date())
		self.download_folder = f'./files/{self.today}/'

		self.CHROMEDRIVER_URL = "c:\chromedriver.exe"
		self.WINDOW_SIZE = "1920,1080"
		self.DOWNLOAD_URL = f'C:\\Users\\Weronika\\Desktop\\Intrinsic_Value\\Vanguard\\files\\{self.today}\\'

		self.df = self.get_data_for(self.funds[0])


	def remove_folders(self):
		for folder in os.listdir('./files'):
			if self.today not in folder:
				shutil.rmtree('./files/' + folder)


	def check_if_downloaded(self, fund_name):
		if not os.path.exists(self.download_folder):
			self.remove_folders()
			os.makedirs(self.download_folder)
			
		l = [x for x in os.listdir(self.download_folder) if fund_name in x]
		
		if len(l) > 0:
			return True
		else:
			return False


	def get_list_of_funds(self):
		with open('./funds.txt', 'r') as file:
			for line in file:
				name, link = line.split('#')
				self.funds_list[name] = link
		return list(self.funds_list.keys())


	def clean_df(self, df):
		df['Date'] = pd.to_datetime(df['Date'])
		df[df.columns[1]] = df[df.columns[1]].str.replace('£', '')
		df[df.columns[1]] = df[df.columns[1]].str.replace('CHF', '')
		df[df.columns[1]] = df[df.columns[1]].str.replace('€', '')
		df[df.columns[1]] = df[df.columns[1]].str.replace('$', '')
		df[df.columns[1]] = df[df.columns[1]].str.replace('A', '')
		df[df.columns[1]] = df[df.columns[1]].astype(float)
		return df
	

	def get_data_for(self, chosen_fund):
		link = self.funds_list[chosen_fund]
	
		if not self.check_if_downloaded(chosen_fund):
			print('Downloading...')
			self.scrap_fund(chosen_fund, link)

		print('Plotting dataframe...')
		df = self.load_fund_df(chosen_fund)
		df = self.clean_df(df)
		
		return df


	def load_fund_df(self, fund_name):        
		l = [x for x in os.listdir(self.download_folder) if fund_name in x]
		df = pd.read_excel(self.download_folder + '/' + l[0], skiprows = 8, error_bad_lines=False)
		return df


	def scrap_fund(self, fund_name, link):
		while True:
			chrome_options = Options()
			chrome_options.add_argument("--headless")
			chrome_options.add_argument("--window-size=%s" % self.WINDOW_SIZE)
			chrome_options.add_experimental_option("prefs", {
					"download.default_directory": self.DOWNLOAD_URL,
					"download.prompt_for_download": False,
					"download.directory_upgrade": True,
					"safebrowsing_for_trusted_sources_enabled": False,
					"safebrowsing.enabled": False
			})

			driver = webdriver.Chrome(executable_path=self.CHROMEDRIVER_URL, options=chrome_options)
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
				continue

			time.sleep(5)
			driver.close()
			print(f'Fund {fund_name} downloaded.')
			return