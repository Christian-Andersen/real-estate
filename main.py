import os
import csv
import atexit
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.window import WindowTypes

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
    try:
        date = datetime.strptime(
            ' '.join(row[-1].split()[-3:]), '%d %b %Y')
        row.append(date.strftime('%Y%m%d'))
    except:
        row.append('-')
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
postcodes = {}
for file in os.listdir('data'):
    path = os.path.join('data', file)
    with open(path, 'r', newline='', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if row[0] != 'id':
                if row[0] in ids:
                    print('Dupe ID found')
                else:
                    ids[row[0]] = row[2]
            date = row[6]
    postcodes[file.split('.')[0]] = os.path.getsize(path)
print('Total Properties:', len(ids))
print('Total Postcodes:', len(postcodes))

# Use postcoes to create webpages to scrape
mainpage = 'https://www.domain.com.au/sold-listings/'
webpages = []
while True:
    postcode = min(postcodes, key=postcodes.get) # type: ignore
    webpages.append(mainpage+'?postcode='+postcode)
    postcodes.pop(postcode)
    if len(postcodes) == 0:
        break
print('Total Webpages:', len(webpages))

# Create selenium driver
options = Options()
options.add_argument('-headless')
# driver = webdriver.Firefox(options=options)

# Load in finished postcodes
skip = []
with open('done.txt', 'r') as f:
    for row in f:
        skip.append(row.rstrip())
skip = list(set(skip))

# Scrape them
for webpage in webpages:
    print('Webpage:', webpage)
    pc = webpage[webpage.find('postcode=')+9:]
    if pc in skip:
        print('SKIPPED WEBPAGE')
        continue
    # Get the first webpage
    driver = webdriver.Firefox(options=options)
    driver.get(webpage)
    atexit.register(driver.quit)
    sites = [driver.page_source]
    start_index = len('<strong>')+sites[0].find('<strong>')
    end_index = sites[0].find('</strong>')
    info = sites[0][start_index:end_index].split()
    if info[1] in ['Property', 'Properties']:
        number_of_properties = int(info[0])
        number_of_pages = 1+(number_of_properties//20)
        print('Number of pages:', number_of_pages)
    else:
        print('Failed to find number of properties')
        raise KeyError
    for i in range(2, min(51, number_of_pages+2)):
        if '?' in webpage:
            site = webpage+'&page='+str(i)
        else:
            site = webpage+'?page='+str(i)
        driver.switch_to.new_window(WindowTypes.TAB)
        driver.execute_script(f"window.location.href = '{site}';")
    for window_handle in driver.window_handles:
        driver.switch_to.window(window_handle)
        print(driver.current_url)
        while True:
            if 'No exact matches' in driver.page_source:
                break
            if '"listingsMap":' in driver.page_source:
                sites.append(driver.page_source)
                break
    for site in sites:
        property_dictionary = html_to_dict(site)
        for value in property_dictionary.values():
            if str(value['id']) in ids:
                continue
            postcode = value['listingModel']['address']['postcode']
            file = os.path.join('data', postcode+'.csv')
            if not os.path.isfile(file):
                with open(file, 'w', newline='', encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(header)
            ids[str(value['id'])] = value['listingModel']['url']
            row = value_to_row(value)
            with open(file, 'a', newline='', encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(row)
    driver.quit()
    with open('done.txt', 'a') as f:
        if 'postcode=' in webpage:
            f.write(pc+'\n')
