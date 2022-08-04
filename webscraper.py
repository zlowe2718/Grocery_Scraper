import bs4, requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import time

class webscraper:

	def __init__(self, zipcode, **kwargs):
		if kwargs:
			self._address 	= kwargs["address"]
		
		self._zipcode 		= zipcode
		self._kroger 		= {"url" : "https://www.kroger.com/", "distance" : 0}
		self._aldi 			= {"url" : "https://www.aldi.us/", "distance" : 0}
		self._sprouts 		= {"url" : "https://www.sprouts.com/", "distance" : 0}

	def wait(self, website, seconds, selector):
		element = WebDriverWait(website, seconds).until(
			EC.presence_of_element_located((By.CSS_SELECTOR, selector))
		)
		return element

	def init_driver(self):
		options = webdriver.ChromeOptions()
		options.add_argument("--window-size=1920,1080")
		options.add_argument("--disable-blink-features=AutomationControlled")
		driver = webdriver.Chrome(options = options)
		return driver

	def scrape_kroger(self, grocery_list):
		#initializes website
		website = self.init_driver()
		website.get(self._kroger["url"])

		#closes kroger pop up add
		if len(website.find_elements(By.CSS_SELECTOR, "button.kds-DismissalButton.kds-Modal-closeButton")) != 0:
			close_pop_up = website.find_element(By.CSS_SELECTOR, "button.kds-DismissalButton.kds-Modal-closeButton")
			close_pop_up.click()
			time.sleep(3)
		
		#finds the pickup location element and clicks on it
		pickup_location = website.find_element(By.CSS_SELECTOR, "span.kds-Text--m.font-500.underline.CurrentModality-vanityName").click()
		time.sleep(3)

		#finds the seacrh_bar for the zipcode element
		try:
			search_zipcode = WebDriverWait(website, 10).until(
				EC.presence_of_element_located((By.CSS_SELECTOR, "input.kds-Input.kds-Input--compact.kds-SolitarySearch-input.kds-Input--search.min-w-0"))
			)
		except TimeoutException:
			website.quit()
			return "Kroger website was slow to respond"

		search_zipcode.clear()
		search_zipcode.send_keys(self._zipcode, Keys.ENTER)
		time.sleep(3)

		#finds the select_store element
		select_store = website.find_element(By.CSS_SELECTOR, "button.kds-Button.kds-Button--primary.kds-Button--compact.AvailableModality--Button.mt-0")
		select_store.send_keys(Keys.ENTER)
		time.sleep(3)

		#since there are multiple stores we have to use find_elements
		stores = website.find_elements(By.CSS_SELECTOR, "button[data-testid*='SelectStore']")
	
		#updates distance from store
		soup = bs4.BeautifulSoup(website.page_source, "html.parser")
		distance = soup.find_all("div", class_= "kds-Text--s text-default-600 sm:pl-0 pt-4" )

		#gets first result(should be the closest) bs4 find_all returns a list of tags, so distance[0] is still a bs4 tag
		#meaning .string needs to be called before slicing
		self._kroger["distance"] = float(distance[0].string[:4])

		#selects the closest store and finds the search bar
		stores[0].click()
		time.sleep(5)
		search_bar = website.find_element(By.CSS_SELECTOR, "input[data-testid*='SearchBar-input']")

		#finds and returns first 5 results and their prices for each grocery in the list
		updated_grocery_list = []
		for grocery in grocery_list.grocery_list:
			search_bar.send_keys(grocery["item"], Keys.ENTER)

			time.sleep(5)
			element = WebDriverWait(website, 20).until(
				EC.presence_of_element_located((By.CSS_SELECTOR, "mark.kds-Price-promotional.kds-Price-promotional--plain.kds-Price-promotional--decorated"))
			)
			#new soup call for new html loaded
			soup = bs4.BeautifulSoup(website.page_source, "html.parser")
			time.sleep(5)

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
			
		website.quit()
		return updated_grocery_list

	
	def scrape_aldi(self, grocery_list):
	#initializes website
		website = self.init_driver()
		website.get(self._aldi["url"])

		choose_store = website.find_element(By.CSS_SELECTOR, "a.top-nav-list-element-link").click()
		time.sleep(3)
		search_store = website.find_element(By.CSS_SELECTOR, "input#DirectorySearchInput")
		search_store.send_keys(self._zipcode, Keys.ENTER)
		time.sleep(3)

		stores = website.find_elements(By.CSS_SELECTOR, "a[data-ya-track='visitpage']")
		stores[0].click()
		time.sleep(5)
		
		shop_online = website.find_element(By.CSS_SELECTOR, "a.Hero-cta.Hero-cta--primary").click()
		time.sleep(3)
		search_bar = website.find_element(By.CSS_SELECTOR, "input[aria-describedby='search-term-accessibility-navigation']")
		updated_grocery_list = []
		for grocery in grocery_list.grocery_list:
			search_bar.send_keys(grocery["item"], Keys.ENTER)

			time.sleep(5)
			element = WebDriverWait(website, 20).until(
				EC.presence_of_element_located((By.CSS_SELECTOR, "div.css-15uwigl"))
			)
			#new soup call for new html loaded
			soup = bs4.BeautifulSoup(website.page_source, "html.parser")
			time.sleep(5)
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
			search_bar = website.find_element(By.CSS_SELECTOR, "input[aria-describedby='search-term-accessibility-navigation']")

			#.clear does not work for this box so a manual copy all and delete is needed to avoid appending
			ActionChains(website).key_down(Keys.CONTROL, search_bar).send_keys("a").key_down(Keys.DELETE, search_bar).key_up(Keys.DELETE, search_bar).key_up(Keys.CONTROL, search_bar).perform()
			
		website.quit()
		return updated_grocery_list


	def scrape_sprouts(self, grocery_list):
	#initializes website
		website = self.init_driver()
		website.get(self._sprouts["url"])

		time.sleep(3)
		choose_store = website.find_element(By.CSS_SELECTOR, "span.spr-store").click()
		time.sleep(3)

		find_store = website.find_elements(By.CSS_SELECTOR, "button img")
		find_store[1].click()
		time.sleep(3)

		search_store = website.find_element(By.CSS_SELECTOR, "input[name='terms']")
		search_store.send_keys(self._zipcode, Keys.ENTER)
		time.sleep(3)

		stores = website.find_elements(By.CSS_SELECTOR, "button.button.small.hollow")
		stores[0].click()
		time.sleep(5)

		search = website.find_element(By.CSS_SELECTOR, "div[aria-label='Search']").click()
		time.sleep(3)

		search_bar = website.find_elements(By.CSS_SELECTOR, "input[name='nav-search']")

		#There's apparently a hidden search bar in the code before this one
		search_bar = search_bar[1]
		updated_grocery_list = []

		for grocery in grocery_list.grocery_list:
			search_bar.send_keys(grocery["item"], Keys.ENTER)
			time.sleep(5)
			
			#pop up, find elements returns an empty list instead of an error
			#if no objects are found
			if len(website.find_elements(By.CSS_SELECTOR, "button.close"))!= 0:
				website.find_elements(By.CSS_SELECTOR, "button.close")[0].click()

			element = WebDriverWait(website, 20).until(
				EC.presence_of_element_located((By.CSS_SELECTOR, "span.css-coqxwd"))
			)
			#new soup call for new html loaded
			soup = bs4.BeautifulSoup(website.page_source, "html.parser")
			time.sleep(5)
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
			search_bar = website.find_elements(By.CSS_SELECTOR, "input[data-test='search-nav-input']")
			
			#another hidden search bar before this one
			search_bar = search_bar[1]
			
			#.clear does not work for this box so a manual copy all and delete is needed to avoid appending
			ActionChains(website).key_down(Keys.CONTROL, search_bar).send_keys("a").key_down(Keys.DELETE, search_bar).key_up(Keys.DELETE, search_bar).key_up(Keys.CONTROL, search_bar).perform()
			
		website.quit()
		return updated_grocery_list
