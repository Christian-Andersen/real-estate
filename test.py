from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)

driver.get('https://www.domain.com.au/sold-listings/')
print(driver.page_source.find('"listingsMap":'))

driver.get('https://www.domain.com.au/sold-listings/')
print(driver.page_source.find('"listingsMap":'))
