import csv
import json
import atexit
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


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
    return  json.loads(s[start_index:end_index+1])


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

# Get information from the data folder
df = pd.read_csv('all.csv', dtype=object)
print('Number of properties:', len(df))
df['date'] = df['date'].astype(float)
# Load in ids
ids = set(df['id'])
# Load in done webpages
with open('loaded.txt', 'r', encoding='utf-8') as f:
    loaded = {line.strip() for line in f.readlines()}
# Create webpages
with open('toomany.txt', 'r', encoding='utf-8') as f:
    webpages = {line.strip() for line in f.readlines()}
price_ranges = []
for i in range(100):
    price_ranges.append(str(10_000*i)+'-'+str(10_000*i+9_999))
price_ranges.append('1000000-1500000')
price_ranges.append('1500000-any')
# Create selenium driver
options = Options()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)
atexit.register(driver.quit)
# Scrape them
for webpage in webpages:
    for price_range in price_ranges:
        for i in range(1, 51):
            url = webpage+'&price='+price_range+'&page='+str(i)
            if url in loaded:
                continue
            print(url)
            last_page = False
            driver.get(url)
            if 'The requested URL was not found on the server.' in driver.page_source:
                print('URL not found: '+url)
                raise
            elif 'No exact matches' in driver.page_source:
                loaded.add(url)
                with open('loaded.txt', 'a', encoding='utf-8') as f:
                    f.write(url+'\n')
                break
            elif i == 1:
                search_string = '"searchResultCount":'
                start = driver.page_source.find(search_string)+len(search_string)
                end = driver.page_source[start:].find(',')
                number_of_properties = int(driver.page_source[start:start+end])
                print('Number of Properties:', number_of_properties)
                if number_of_properties <= 20:
                    last_page = True
                elif number_of_properties > 1_000:
                    print('Over 1000 properties at URL: '+url)
                    raise
            property_dictionary = html_to_dict(driver.page_source)
            for value in property_dictionary.values():
                if str(value['id']) in ids:
                    continue
                ids.add(str(value['id']))
                row = value_to_row(value)
                with open('all.csv', 'a', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(row)
            loaded.add(url)
            with open('loaded.txt', 'a', encoding='utf-8') as f:
                f.write(url+'\n')
            if last_page:
                break
