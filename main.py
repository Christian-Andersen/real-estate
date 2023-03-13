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
# Create selenium driver
options = Options()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)
atexit.register(driver.quit)
# Scrape them
while True:
    suburb = max(suburbs, key=suburbs.get) # type: ignore
    main_webpage = 'https://www.domain.com.au/sold-listings/'+look_up[suburb]+'/?excludepricewithheld=1&ssubs=0&page='
    url = False
    for i in range(1, 51):
        webpage = main_webpage+str(i)
        if webpage not in loaded:
            url = webpage
            break
    if not url:
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write('All pages have been loaded: '+main_webpage+'\n')
        continue
    year = str(suburbs[suburb])[0:4]
    month = str(suburbs[suburb])[4:6]
    day = str(suburbs[suburb])[6:8]
    print(f'{day}/{month}/{year} : {suburb: <30} - {url}')
    driver.get(url)
    if 'The requested URL was not found on the server.' in driver.page_source:
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write('URL not found: '+url+'\n')
        suburbs.pop(suburb)
    elif 'No exact matches' in driver.page_source:
        if 'page=1' in url:
            with open('log.txt', 'a', encoding='utf-8') as f:
                f.write('Not properties in suburb: '+url+'\n')
        else:
            with open('finished_suburbs.txt', 'a', encoding='utf-8') as f:
                f.write(suburb+'\n')
        suburbs.pop(suburb)
    else:
        property_dictionary = html_to_dict(driver.page_source)
        for value in property_dictionary.values():
            if str(value['id']) in ids:
                continue
            ids.add(str(value['id']))
            row = value_to_row(value)
            if row[6] != '':
                date = float(row[6])
                if row[8] not in suburbs:
                    suburbs[row[8]] = date
                elif date < suburbs[row[8]]:
                    suburbs[row[8]] = date
            with open('all.csv', 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(row)
        if len(property_dictionary.values()) < 20:
            with open('finished_suburbs.txt', 'a', encoding='utf-8') as f:
                f.write(suburb+'\n')
            suburbs.pop(suburb)
    loaded.add(url)
    with open('loaded.txt', 'a', encoding='utf-8') as f:
        f.write(url+'\n')
