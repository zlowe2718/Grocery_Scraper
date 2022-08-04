import bs4, requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time

class webscraper:

	def __init__(self):
		with open("settings.json", "r") as fh:
			self.settings = json.load(fh)
		self.kroger 		= {"url" : "https://www.kroger.com/", "distance" : 0}
		self.aldi 			= {"url" : "https://www.aldi.us/", "distance" : 0}
		self.sprouts 		= {"url" : "https://www.sprouts.com/", "distance" : 0}


	def wait_for_element(self, selector):
		element = WebDriverWait(self.website, self.settings["seconds"]).until(
			EC.presence_of_element_located((By.CSS_SELECTOR, selector))
		)
		return element


	def wait_for_elements(self, selector):
		elements = WebDriverWait(self.website, self.settings["seconds"]).until(
			EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
		)
		return elements


	def wait_for_clickable_element(self, selector):
		WebDriverWait(self.website, self.settings["seconds"]).until(
			EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
		)


	def init_driver(self):
		options = webdriver.ChromeOptions()
		options.add_argument("--window-size=1920,1080")
		options.add_argument("--disable-blink-features=AutomationControlled")
		driver = webdriver.Chrome(options = options)
		return driver

	def scrape_kroger(self, grocery_list):
		#initializes website
		website = self.init_driver()
		website.get(self.kroger["url"])
		self.website = website

		try:
			#closes kroger pop up add
			if len(self.wait_for_elements("button.kds-DismissalButton.kds-Modal-closeButton")) != 0:
				close_pop_up = website.find_element(By.CSS_SELECTOR, "button.kds-DismissalButton.kds-Modal-closeButton")
				close_pop_up.click()
			
			#finds the pickup location element and clicks on it
			pickup_location = self.wait_for_element("span.kds-Text--m.font-500.underline.CurrentModality-vanityName").click()
	
			#finds the search_bar for the zipcode element
			search_zipcode = self.wait_for_element("input.kds-Input.kds-Input--compact.kds-SolitarySearch-input.kds-Input--search.min-w-0")
			search_zipcode.clear()
			search_zipcode.send_keys(self.settings["zipcode"], Keys.ENTER)
	
			#finds the select_store element
			select_store = self.wait_for_element("button.kds-Button.kds-Button--primary.kds-Button--compact.AvailableModality--Button.mt-0")
			select_store.send_keys(Keys.ENTER)
	
			#since there are multiple stores we have to use find_elements
			stores = self.wait_for_elements("button[data-testid*='SelectStore']")
		
			#updates distance from store
			soup = bs4.BeautifulSoup(website.page_source, "html.parser")
			distance = soup.find_all("div", class_= "kds-Text--s text-default-600 sm:pl-0 pt-4" )
	
			#gets first result(should be the closest) bs4 find_all returns a list of tags, so distance[0] is still a bs4 tag
			#meaning .string needs to be called before slicing
			self.kroger["distance"] = float(distance[0].string[:4])
	
			#selects the closest store and finds the search bar
			stores[0].click()

			search_bar = self.wait_for_element("input[data-testid*='SearchBar-input']")
	
			#finds and returns first 5 results and their prices for each grocery in the list
			updated_grocery_list = []
			for grocery in grocery_list.grocery_list:
				search_bar.send_keys(grocery["item"], Keys.ENTER)
				
				#waits for website to update before waiting for element.
				#if no wait is specified then the code continues to run before
				#the site javascript is updated
				time.sleep(1)
				element = self.wait_for_element("mark.kds-Price-promotional.kds-Price-promotional--plain.kds-Price-promotional--decorated")

				#new soup call for new html loaded
				soup = bs4.BeautifulSoup(website.page_source, "html.parser")
	
				#finds all names and prices for every card loaded
				all_dollars = soup.find_all("span", class_="kds-Price-promotional-dropCaps")
				all_cents = soup.find_all("sup", class_="kds-Price-superscript")
				all_names = soup.find_all("h3", class_="kds-Text--l text-default-900 font-secondary font-500 mt-8 mb-0")
				results = {grocery["item"] : []}
	
				#returns the first 5 results into a dictionary
				for i in range(0,5):
					dollars = all_dollars[i].string
					name = all_names[i].string
					cents = ""
	
					#returns . then cents number so if the value was 23 cents it retuerns .23
					for string in all_cents[2 * i + 1].stripped_strings:
						cents += string
					
					results[grocery["item"]].append({"item" : name, "price" : float(dollars + cents)})
				
				updated_grocery_list.append(results)
	
				#.clear does not work for this box so a manual copy all and delete is needed to avoid appending
				ActionChains(website).key_down(Keys.CONTROL, search_bar).send_keys("a").key_down(Keys.DELETE, search_bar).key_up(Keys.DELETE, search_bar).key_up(Keys.CONTROL, search_bar).perform()
		except TimeoutException:
			website.quit()
			return "Kroger was too slow to respond"		
		website.quit()
		return updated_grocery_list

	
	def scrape_aldi(self, grocery_list):
	#initializes website
		website = self.init_driver()
		website.get(self.aldi["url"])
		self.website = website
		try:
			choose_store = self.wait_for_element("a.top-nav-list-element-link").click()
	
			search_store = self.wait_for_element("input#DirectorySearchInput")
			search_store.send_keys(self.settings["zipcode"], Keys.ENTER)
	
			stores = self.wait_for_elements("a[data-ya-track='visitpage']")
			stores[0].click()
			
			shop_online = self.wait_for_element("a.Hero-cta.Hero-cta--primary").click()
	
			search_bar = self.wait_for_element("input[aria-describedby='search-term-accessibility-navigation']")
	
			updated_grocery_list = []
			for grocery in grocery_list.grocery_list:
				search_bar.send_keys(grocery["item"], Keys.ENTER)
	
				time.sleep(1)
				element = self.wait_for_element("span.css-coqxwd")
	
				#new soup call for new html loaded
				soup = bs4.BeautifulSoup(website.page_source, "html.parser")

				all_prices = soup.find_all("span", class_="css-coqxwd")
				
				all_names = soup.find_all("div", class_="css-15uwigl")
				results = {grocery["item"] : []}
	
				#returns the first 5 results into a dictionary
				for i in range(0,5):
					price = all_prices[i].string[1:5]
					name = all_names[i].string			
					results[grocery["item"]].append({"item" : name, "price" : price})
				
				updated_grocery_list.append(results)
				
				#stale element reference so search_bar node needs to be updated each search
				search_bar = self.wait_for_element("input[aria-describedby='search-term-accessibility-navigation']")
	
				#.clear does not work for this box so a manual copy all and delete is needed to avoid appending
				ActionChains(website).key_down(Keys.CONTROL, search_bar).send_keys("a").key_down(Keys.DELETE, search_bar).key_up(Keys.DELETE, search_bar).key_up(Keys.CONTROL, search_bar).perform()
		except TimeoutException:
			website.quit()
			return "Aldi was too slow to respond."	
		website.quit()
		return updated_grocery_list


	def scrape_sprouts(self, grocery_list):
	#initializes website
		website = self.init_driver()
		website.get(self.sprouts["url"])
		self.website = website

		try:
			#sometimes the website javascript is finicky, so the extra waits are added to
			#ensure the code continues to run
			time.sleep(1)
			choose_store = website.find_element(By.CSS_SELECTOR, "a span.spr-store")
			self.wait_for_clickable_element("span.spr-store")
			choose_store.click()

			find_store = self.wait_for_elements("button img")
			self.wait_for_clickable_element("button img")
			find_store[1].click()

			search_store = self.wait_for_element("input[name='terms']")
			self.wait_for_clickable_element("input[name='terms']")
			search_store.send_keys(self.settings["zipcode"], Keys.ENTER)
	
			stores = self.wait_for_elements("button.button.small.hollow")
			stores[0].click()
	
			search = self.wait_for_element("div[aria-label='Search']").click()
	
			search_bar = self.wait_for_elements("input[name='nav-search']")
	
			#There's a hidden search bar in the html code before this one
			search_bar = search_bar[1]
			updated_grocery_list = []
	
			for grocery in grocery_list.grocery_list:
				search_bar.send_keys(grocery["item"], Keys.ENTER)
				
				time.sleep(1)
				
				#pop up only appears once
				if grocery == grocery_list.grocery_list[0]:
					self.wait_for_elements("button.close")[0].click()
	
				element = self.wait_for_element("span.css-coqxwd")

				#new soup call for new html loaded
				soup = bs4.BeautifulSoup(website.page_source, "html.parser")

				all_prices = soup.find_all("span", class_="css-coqxwd")
				all_names = soup.find_all("div", class_="css-f85de")
				results = {grocery["item"] : []}
	
				#returns the first 5 results into a dictionary
				for i in range(0,5):
					price = all_prices[i].string[1:5]
					name = all_names[i].string			
					results[grocery["item"]].append({"item" : name, "price" : price})
				
				updated_grocery_list.append(results)
				
				#stale element reference so search_bar node needs to be updated each search
				search_bar = self.wait_for_elements("input[data-test='search-nav-input']")
				
				#another hidden search bar before this one
				search_bar = search_bar[1]
				
				#.clear does not work for this box so a manual copy all and delete is needed to avoid appending
				ActionChains(website).key_down(Keys.CONTROL, search_bar).send_keys("a").key_down(Keys.DELETE, search_bar).key_up(Keys.DELETE, search_bar).key_up(Keys.CONTROL, search_bar).perform()
		except TimeoutException:
			website.quit()
			return "Sprouts was too slow to respond"

		website.quit()
		return updated_grocery_list
