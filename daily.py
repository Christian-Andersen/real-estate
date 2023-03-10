import os
import csv
import time
import atexit
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.window import WindowTypes

def add_column(group, header):
    """Returns '' if the key 'header' does not excist in dict 'group'"""
    if header in group:
        return group[header]
    else:
        return ''


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
    if row[-1] == 'Price Withheld':
        row[-1] = ''
    elif row[-1].startswith('$'):
        row[-1] = row[-1][1:].replace(',', '')
    row.append(value['listingModel']['tags']['tagClassName'])
    row.append(value['listingModel']['tags']['tagText'])
    try:
        date = datetime.strptime(
            ' '.join(row[-1].split()[-3:]), '%d %b %Y')
        row.append(date.strftime('%Y%m%d'))
    except:
        row.append('')
    address = value['listingModel']['address']
    row.append(add_column(address, 'street').replace('\n', ' '))
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

# File Check
for filename in os.listdir('data'):
    path = os.path.join('data', filename)
    for line in open(path, 'r', encoding='utf-8'):
        if not line.startswith('id'):
            int(line[:10])
# Get information from the data folder
ids = {}
for filename in os.listdir('data'):
    path = os.path.join('data', filename)
    with open(path, 'r', newline='', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if row[0] != 'id':
                if row[0] in ids:
                    print('Dupe ID found')
                else:
                    ids[row[0]] = row[2]
print('Total Properties:', len(ids))

# Load in finished postcodes
skip = []
with open('done.txt', 'r') as f:
    for row in f:
        skip.append(row.rstrip())
skip = list(set(skip))

# Use postcoes to create webpages to scrape
mainpage = 'https://www.domain.com.au/sold-listings/'
webpages = [mainpage]
states = ['nt', 'nsw', 'act', 'vic', 'qld', 'sa', 'wa', 'tas']
for state in states:
    webpages.append(mainpage+'?state='+state)
print('Total Webpages:', len(webpages))

# Create selenium driver
options = Options()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)
atexit.register(driver.quit)

# Scrape them
for webpage in webpages:
    print('\nWebpage:', webpage)
    for i in range(1, 51):
        if '?' in webpage:
            site = webpage+'&page='+str(i)
        else:
            site = webpage+'?page='+str(i)
        print(site, end='\t')
        driver.get(site)
        print('Done', end='\t')
        page_data = driver.page_source
        if page_data.find('"listingsMap":') == -1:
            print('FAILED TO FIND DATA ON WEBAGE:', site)
            continue
        property_dictionary = html_to_dict(page_data)
        dupes = 0
        for value in property_dictionary.values():
            if str(value['id']) in ids:
                dupes += 1
                continue
            postcode = value['listingModel']['address']['postcode']
            file = os.path.join('data', postcode+'.csv')
            if not os.path.isfile(file):
                with open(file, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(header)
            ids[str(value['id'])] = value['listingModel']['url']
            row = value_to_row(value)
            with open(file, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(row)
        print(dupes)
