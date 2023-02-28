import os
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


def add_column(group, header):
    """Returns '-' if the key 'header' does not excist in dict 'group'"""
    if header in group:
        return group[header]
    else:
        return '-'


def get_site(url):
    """Grabs the site from url input"""
    # Configure headless Firefox options
    options = Options()
    options.add_argument('-headless')

    # Create a new instance of the Firefox driver with the configured options
    driver = webdriver.Firefox(options=options)

    # Navigate to the URL
    driver.get(url)

    # Retrieve the HTML content of the page
    html_content = driver.page_source

    # Close the browser
    driver.quit()

    # Process the HTML content as needed
    return html_content


def html_to_dict(s):
    """Converts a domain.com.au search to a list of property information"""
    true = True
    false = False
    null = None
    search = '"listingsMap":'
    start_index = s.find(search)+len(search)
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
ids = []
urls = []
for file in os.listdir('data'):
    path = os.path.join('data', file)
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

for i in range(1, 50+1):
    print('Page:', i)
    webpage = 'https://www.domain.com.au/sold-listings/?state=qld&page='+str(i)
    s = get_site(webpage)
    d = html_to_dict(s)
    for value in d.values():
        if 'postcode' in value['listingModel']['address']:
            postcode = value['listingModel']['address']['postcode']
        else:
            postcode = 'unknown'
        file = os.path.join('data', postcode+'.csv')
        if not os.path.isfile(file):
            with open(file, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(header)
        with open(file, 'a', newline='') as f:
            w = csv.writer(f)
            if (str(value['id']) in ids) and (value['listingModel']['url'] in urls):
                print('Dupe found and skipped')
                continue
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
            ids.append(value['id'])
            urls.append(value['listingModel']['url'])
            w.writerow(row)
