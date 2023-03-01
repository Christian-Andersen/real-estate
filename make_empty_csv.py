import time
import os
import csv
import atexit
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


header = [
    'id',
    'listingType',
    'url',
    'price',
    'tagClassName',
    'tagText',
    'date',
    'street',
    'suburb',
    'state',
    'postcode',
    'lat',
    'lng',
    'beds',
    'baths',
    'parking',
    'propertyType',
    'propertyTypeFormatted',
    'isRural',
    'landSize',
    'landUnit',
    'isRetirement'
]

# Create selenium driver
options = Options()
options.add_argument('-headless')
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(options=options, service=service)
atexit.register(driver.quit)

# Scrape them
for i in range(1300, 10_000):
    postcode = f'{i:0>4}'
    site = 'https://www.domain.com.au/sold-listings/?postcode='+postcode
    failed_get_site = True
    for _ in range(10):
        try:
            driver.get(site)
            failed_get_site = False
            break
        except Exception as e:
            print(e)
    if failed_get_site:
        print('\nFAILED TO GET SITE\n'+site+'\n')
    else:
        html_content = driver.page_source
        if 'No exact matches' in html_content:
            print(postcode+' - no properties found'+40*' ', end='\r')
        else:
            file = os.path.join('data', str(postcode)+'.csv')
            if os.path.isfile(file):
                print(postcode+' - CSV already exists'+40*' ')
            else:
                with open(file, 'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(header)
                print(postcode+' - made the CSV with header'+40*' ')
