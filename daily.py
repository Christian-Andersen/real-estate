"""
Daily update scraper for Domain.com.au.
Scrapes the most recent sold listings to keep the database up to date.
"""

import atexit
import csv
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from utils import html_to_dict, value_to_row

header = [
    "id",
    "listingType",
    "url",
    "price",
    "tagClassName",
    "tagText",
    "date",
    "street",
    "suburb",
    "state",
    "postcode",
    "lat",
    "lng",
    "beds",
    "baths",
    "parking",
    "propertyType",
    "propertyTypeFormatted",
    "isRural",
    "landSize",
    "landUnit",
    "isRetirement",
]

# Get information from the data folder
all_csv = Path("all.csv")
if all_csv.exists():
    df = pd.read_csv(all_csv, dtype=object)
    print("Number of properties:", len(df))
    df["date"] = df["date"].astype(float)
    # Load in ids
    ids = set(df["id"])
    # Load in suburbs
    suburbs = df.groupby("suburb")["date"].min().to_dict()
    # Make look up dict
    series = (
        df["suburb"].str.replace(" ", "-").str.replace("'", "-") + "-" + df["state"] + "-" + df["postcode"]
    ).str.lower()
    look_up = dict(zip(df["suburb"], series, strict=False))
else:
    print("all.csv not found. Starting with empty data.")
    ids = set()
    suburbs = {}
    look_up = {}
    with all_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)

# Load in done webpages
loaded_file = Path("loaded.txt")
if loaded_file.exists():
    with loaded_file.open(encoding="utf-8") as f:
        loaded = {line.strip() for line in f}
else:
    loaded = set()

# Load in finished suburbs
finished_suburbs_file = Path("finished_suburbs.txt")
if finished_suburbs_file.exists():
    with finished_suburbs_file.open(encoding="utf-8") as f:
        finished_suburbs = {line.strip() for line in f}
else:
    finished_suburbs = set()

for finished_suburb in finished_suburbs:
    suburbs.pop(finished_suburb, None)

# Create webpages
mainpage = "https://www.domain.com.au/sold-listings/?excludepricewithheld=1&ssubs=0"
webpages = [mainpage]
states = ["nt", "nsw", "act", "vic", "qld", "sa", "wa", "tas"]
webpages.extend(mainpage + "&state=" + state for state in states)
print("Total Webpages:", len(webpages))

# Create selenium driver
options = Options()
options.add_argument("-headless")
driver = webdriver.Firefox(options=options)
atexit.register(driver.quit)

# Scrape them
for webpage in webpages:
    for i in range(1, 51):
        url = webpage + "&page=" + str(i)
        print(url, end="")
        driver.get(url)
        property_dictionary = html_to_dict(driver.page_source)
        dupes = 0
        for value in property_dictionary.values():
            if str(value["id"]) in ids:
                dupes += 1
                continue
            ids.add(str(value["id"]))
            row = value_to_row(value)
            date = float(row[6])
            if row[8] not in suburbs or date < suburbs[row[8]]:
                suburbs[row[8]] = date
            with Path("all.csv").open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(row)
        print(" \tDupes:", dupes)
