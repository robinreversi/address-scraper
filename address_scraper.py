import re
import time

import labels
from reportlab.graphics import shapes
from reportlab.pdfbase.pdfmetrics import stringWidth
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

def scrapePropertyPage(propertyPage, mailingInfo):
	try:
		propAddress = propertyPage.find(string = 'Address:').next_element.get_text()
		ownerName = propertyPage.find(string = 'Name:').next_element.get_text()
		mailAddress = propertyPage.find(string = 'Mailing Address:').next_element.get_text()

		data = ownerName + '<br />' + propAddress

		mailingInfo.append(data)

		if propAddress != mailAddress:
			data = ownerName + '<br />' + mailAddress
			mailingInfo.append(data)

	except AttributeError as e:
		print('Could not process page')


def scrapeListings(driver, propertyListings, mailingInfo):
	for link in propertyListings.findAll('a', href = re.compile('(P|p)roperty\.aspx\?prop\_id=[0-9]*')):
		driver.get('http://www.bcad.org/ClientDB/' + link.attrs['href'])
		propertyPage = BeautifulSoup(driver.page_source, 'html.parser')
		scrapePropertyPage(propertyPage, mailingInfo)

def scrape(driver, mailingInfo, pageNum):
	propertyListings = BeautifulSoup(driver.page_source, 'html.parser')
	pageNum = pageNum + 1
	nextPage = propertyListings.find('a', href = 'SearchResults.aspx?rtype=address&page=' + str(pageNum))
	scrapeListings(driver, propertyListings, mailingInfo)
	if nextPage:
		print(nextPage.attrs['href'])
		driver.get('http://www.bcad.org/ClientDB/' + nextPage.attrs['href'])
		scrape(driver, mailingInfo, pageNum)

def set_search_type(driver):
	select = Select(driver.find_element_by_id('propertySearchOptions_searchType'))
	optionMap = {}
	for index, option in enumerate(select.options):
		optionMap[str(index + 1)] = option.get_attribute('value')
		print(str(index + 1) + ': ' + option.get_attribute('value'))

	searchType = input('Choose an option (numbers only) :' + '\n')

	while searchType not in optionMap:
		searchType = input('Invalid Option. Try again.' + '\n')
	
	select.select_by_visible_text(optionMap[searchType])

def set_query(driver):	
	inputNames = driver.find_elements_by_xpath('//table[@style = "display: block;"]//td[@class = "formLabel"]')
	inputFields = driver.find_elements_by_xpath('//table[@style = "display: block;"]//input')

	for name, field in zip(inputNames, inputFields):
		response = input(name.text + ' ' + '\n')
		field.send_keys(response)

def run_scraper():
	driver = webdriver.PhantomJS(executable_path = '/Users/robincheong/Downloads/phantomjs-2.1.1-macosx/bin/phantomjs')
	driver.get('http://www.bcad.org/clientdb/PropertySearch.aspx?cid=1')

	set_search_type(driver)
	set_query(driver)

	driver.find_element_by_id('propertySearchOptions_search').click()
	
	mailingInfo = []

	scrape(driver, mailingInfo, 1)

	driver.close()

	return mailingInfo

def drawLabel(label, width, height, obj):
		str_obj = str(obj)
		font_size = 50
		text_width = width - 10
		while stringWidth(str_obj, 'Helvetica', font_size) > text_width:
			font_size = font_size * .9

		label.add(shapes.String(width/2, height/2, str_obj, fontName = 'Helvetica', fontSize = font_size, textAnchor = 'middle'))

def generate_labels():
	mailingInfo = run_scraper()

	specs = labels.Specification(215.9, 279.4, 3, 10, 66.7, 25.4, corner_radius = 2)

	sheet = labels.Sheet(specs, drawLabel, border = True)

	sheet.add_labels(mailingInfo)

	sheet.save('mailing_labels.pdf')
	print('done!')

generate_labels()

