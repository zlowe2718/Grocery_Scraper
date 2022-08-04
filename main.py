from webscraper import webscraper
from groceries import groceries
from selenium import webdriver
from pandas import DataFrame
from selenium.common.exceptions import TimeoutException
import numpy as np
import json

scraper = webscraper()

groceries = groceries()

#add your groceries here!
groceries.add_groceries(["Banana", "Orange", "Apple"])

#tries each website twice in case something doesnt load in time
try:
	kroger_results = scraper.scrape_kroger(groceries)
except TimeoutException:
	try:
		kroger_results = scraper.scrape_kroger(groceries)
	except TimeoutException:
		kroger_results =[]
try:
	aldi_results = scraper.scrape_aldi(groceries)
except TimeoutException:
	try:
		aldi_results = scraper.scrape_aldi(groceries)
	except TimeoutException:
		aldi_results = []
try:	
	sprouts_results = scraper.scrape_sprouts(groceries)
except TimeoutException:
	try:
		sprouts_results = scraper.scrape_sprouts(groceries)
	except TimeoutException:
		sprouts_results = []

with open("settings.json", "r") as fh:
	settings = json.load(fh)

#compiles data into a list of lists
data_list = []
for groc_ind in range(len(groceries.grocery_list)):
	grocery = groceries.grocery_list[groc_ind]["item"]
	for res_ind in range(settings["results"]):
		if len(kroger_results) != 0:
			data_list.append(["Kroger", grocery, kroger_results[groc_ind][grocery][res_ind]["item"], kroger_results[groc_ind][grocery][res_ind]["price"]])
		if len(aldi_results) != 0:
			data_list.append(["Aldi", grocery, aldi_results[groc_ind][grocery][res_ind]["item"], aldi_results[groc_ind][grocery][res_ind]["price"]])
		if len(sprouts_results) != 0:
			data_list.append(["Sprouts", grocery, sprouts_results[groc_ind][grocery][res_ind]["item"], sprouts_results[groc_ind][grocery][res_ind]["price"]])

data_list = np.array(data_list)
data = {"Store": data_list[:,0], "Grocery": data_list[:,1], "Item Name": data_list[:,2], "Price": data_list[:,3]}

#outputs to csv
df = DataFrame(data = data)
#if desired change output file name here
df.to_csv("output.txt")

