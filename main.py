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


def value_to_row(value):
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
    return row


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
ids = {}
postcodes_first = []
postcodes_second = []
for file in os.listdir('data'):
    path = os.path.join('data', file)
    if 'unknown' not in file:
        if os.path.getsize(path) < 200_000:
            postcodes_first.append(file.split('.')[0])
        else:
            postcodes_second.append(file.split('.')[0])
    with open(path, 'r', newline='') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if row[0] == 'id':
                continue
            elif row[0] in ids:
                print('Dupe id found: ', row[0])
                if ids[row[0]] != row[2]:
                    print(row[0])
                    print(ids[row[0]])
                    print(row[2])
                    raise KeyError("url mismatch for same id")
            else:
                ids[row[0]] = row[2]
print('Total Properties:', len(ids))
print('Total Postcodes:', len(postcodes_first)+len(postcodes_second))

# Use postcoes to create webpages to scrape
webpages = ['https://www.domain.com.au/sold-listings/']
for postcode in postcodes_first:
    webpages.append(
        'https://www.domain.com.au/sold-listings/?postcode='+postcode)
for postcode in postcodes_second:
    webpages.append(
        'https://www.domain.com.au/sold-listings/?postcode='+postcode)
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
    i = 1
    adjust = 1
    while True:
        if '?' in webpage:
            site = webpage+'&page='+str(i)
        else:
            site = webpage+'?page='+str(i)
        print('Page:', i, '\t', 'Properties:', len(ids), '\t'+site)
        failed_get_site = True
        for _ in range(10):
            try:
                driver.get(site)
                failed_get_site = False
                break
            except Exception as e:
                print(e)
        if failed_get_site:
            continue
        html_content = driver.page_source
        if 'No exact matches' in html_content:
            property_dictionary = {}
            if adjust == 1:
                i = 50
        else:
            property_dictionary = html_to_dict(html_content)
        dupes = 0
        for value in property_dictionary.values():
            if str(value['id']) in ids:
                if ids[str(value['id'])] != value['listingModel']['url']:
                    print(str(value['id']))
                    print(ids[str(value['id'])])
                    print(value['listingModel']['url'])
                    raise KeyError("url mismatch for same id")
                dupes += 1
                if dupes == 20:
                    if (adjust == -1):
                        i = 1
                    elif i != 50:
                        i = 51
                        adjust = -1
                    break
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
            ids[str(value['id'])] = value['listingModel']['url']
            row = value_to_row(value)
            with open(file, 'a', newline='') as f:
                w = csv.writer(f)
                w.writerow(row)
        print('Dupes:', dupes)
        if ((i == 50) and (adjust == 1)) or ((i == 1) and (adjust == -1)):
            break
        i += adjust
