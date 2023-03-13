import csv
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

# Get information from the data folder
df = pd.read_csv('all.csv', dtype=object)
print('Number of properties:', len(df))
df['date'] = df['date'].astype(float)
# Load in ids
ids = set(df['id'])
# Load in suburbs
suburbs = df.groupby('suburb')['date'].min().to_dict()
# Make look up dict
series = (df['suburb'].str.replace(' ', '-').str.replace('\'','-')+'-' +
          df['state']+'-'+df['postcode']).str.lower()
look_up = dict(zip(df['suburb'], series))
# Load in done webpages
with open('loaded.txt', 'r', encoding='utf-8') as f:
    loaded = {line.strip() for line in f.readlines()}
# Load in finished suburbs
with open('finished_suburbs.txt', 'r', encoding='utf-8') as f:
    finished_suburbs = {line.strip() for line in f.readlines()}
for finished_suburb in finished_suburbs:
    suburbs.pop(finished_suburb)
# Create webpages
mainpage = 'https://www.domain.com.au/sold-listings/?excludepricewithheld=1&ssubs=0'
webpages = [mainpage]
states = ['nt', 'nsw', 'act', 'vic', 'qld', 'sa', 'wa', 'tas']
for state in states:
    webpages.append(mainpage+'&state='+state)
print('Total Webpages:', len(webpages))
# Create selenium driver
options = Options()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)
atexit.register(driver.quit)
# Scrape them
for webpage in webpages:
    for i in range(1, 51):
        url = webpage+'&page='+str(i)
        print(url, end=' \t')
        driver.get(url)
        if 'The requested URL was not found on the server.' in driver.page_source:
            with open('log.txt', 'a', encoding='utf-8') as f:
                f.write('URL not found: '+url+'\n')
        else:
            property_dictionary = html_to_dict(driver.page_source)
            dupes = 0
            for value in property_dictionary.values():
                if str(value['id']) in ids:
                    dupes += 1
                    continue
                ids.add(str(value['id']))
                row = value_to_row(value)
                date = float(row[6])
                if row[8] not in suburbs:
                    suburbs[row[8]] = date
                elif date < suburbs[row[8]]:
                    suburbs[row[8]] = date
                with open('all.csv', 'a', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(row)
            print('Dupes:', dupes)
