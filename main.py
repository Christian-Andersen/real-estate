import time
import os
import csv
import atexit
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager


def add_column(group, header):
    """Returns '-' if the key 'header' does not excist in dict 'group'"""
    if header in group:
        return group[header]
    else:
        return '-'


def html_to_dict(s):
    """Converts a domain.com.au search to a list of property information"""
    true = True
    false = False
    null = None
    search = '"listingsMap":'
    start_index = s.find(search)
    if start_index == -1:
        return {}
    start_index += len(search)
    end_index = start_index
    count = 0
    while end_index < len(s):
        if s[end_index] == '{':
            count += 1
        elif s[end_index] == '}':
            count += -1
        if count == 0:
            break
        end_index += 1
    return eval(s[start_index:end_index+1])


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

# Get information from the data folder
ids = []
urls = []
postcodes_first = []
postcodes_second = []
for file in os.listdir('data'):
    path = os.path.join('data', file)
    os.path.getsize
    if 'unknown' not in file:
        if ((time.time()-os.path.getmtime(path)) > 32*60*60) or (os.path.getsize(path) < 1000):
            postcodes_first.append(file.split('.')[0])
        else:
            postcodes_second.append(file.split('.')[0])
    with open(path, 'r', newline='') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if row[0] == 'id':
                continue
            if row[0] in ids:
                print('Dupe id found: ', row[0])
            if row[2] in urls:
                print('Dupe url found: ', row[2])
            ids.append(row[0])
            urls.append(row[2])
print('Total Properties:', len(ids))
print('Total Postcodes:', len(postcodes_first)+len(postcodes_second))


# Use postcoes to create webpages to scrape
webpages = ['https://www.domain.com.au/sold-listings/']
webpages = []
for postcode in postcodes_first:
    webpages.append(
        'https://www.domain.com.au/sold-listings/?postcode='+postcode)
for postcode in postcodes_second:
    webpages.append(
        'https://www.domain.com.au/sold-listings/?postcode='+postcode)
webpages = list(set(webpages))
print('Total Webpages:', len(webpages))

# Create selenium driver
options = Options()
options.add_argument('-headless')
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(options=options, service=service)
atexit.register(driver.quit)

# Scrape them
for webpage in webpages:
    print('Webpage:', webpage)
    for i in range(1, 50+1):
        if '?' in webpage:
            site = webpage+'&page='+str(i)
        else:
            site = webpage+'?page='+str(i)
        print('Page:', i, '\t', 'Sites:', len(ids), '\n'+site)
        driver.get(site)
        html_content = driver.page_source
        property_dictionary = html_to_dict(html_content)
        if not property_dictionary:
            with open('failed_sites.txt', 'a') as f:
                f.write(site+'\n')
            continue
        print("FAILED TO FIND DICTIONARY FROM URL\n"+site)
        for value in property_dictionary.values():
            if (str(value['id']) in ids) and (value['listingModel']['url'] in urls):
                print('Dupe found and skipped')
                continue
            if 'postcode' in value['listingModel']['address']:
                postcode = value['listingModel']['address']['postcode']
            else:
                postcode = 'unknown'
            file = os.path.join('data', postcode+'.csv')
            if not os.path.isfile(file):
                with open(file, 'w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(header)
            row = []
            row.append(value['id'])
            row.append(value['listingType'])
            row.append(value['listingModel']['url'])
            row.append(value['listingModel']['price'])
            if row[-1].startswith('$'):
                row[-1] = row[-1][1:].replace(',', '')
            row.append(value['listingModel']['tags']['tagClassName'])
            row.append(value['listingModel']['tags']['tagText'])
            date = datetime.strptime(
                ' '.join(row[-1].split()[-3:]), '%d %b %Y')
            row.append(int(date.strftime('%Y%m%d')))
            address = value['listingModel']['address']
            row.append(add_column(address, 'street'))
            row.append(add_column(address, 'suburb'))
            row.append(add_column(address, 'state'))
            row.append(add_column(address, 'postcode'))
            row.append(add_column(address, 'lat'))
            row.append(add_column(address, 'lng'))
            features = value['listingModel']['features']
            row.append(add_column(features, 'beds'))
            row.append(add_column(features, 'baths'))
            row.append(add_column(features, 'parking'))
            row.append(add_column(features, 'propertyType'))
            row.append(add_column(features, 'propertyTypeFormatted'))
            row.append(add_column(features, 'isRural'))
            row.append(add_column(features, 'landSize'))
            row.append(add_column(features, 'landUnit'))
            if row[-1] == 'm²':
                row[-1] = 'm2'
            row.append(add_column(features, 'isRetirement'))
            ids.append(str(value['id']))
            urls.append(value['listingModel']['url'])
            with open(file, 'a', newline='') as f:
                w = csv.writer(f)
                w.writerow(row)
