"""
Main scraper script for Domain.com.au.
Iterates through suburbs and scrapes sold property data into a CSV file.
"""

import atexit
import csv
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from utils import html_to_dict, value_to_row

PAGE_SIZE_LIMIT = 20

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

# Create selenium driver
options = Options()
options.add_argument("-headless")
driver = webdriver.Firefox(options=options)
atexit.register(driver.quit)

# Scrape them
while True:
    if not suburbs:
        break
    suburb = max(suburbs, key=suburbs.get)  # type: ignore[arg-type]
    main_webpage = (
        "https://www.domain.com.au/sold-listings/" + look_up[suburb] + "/?excludepricewithheld=1&ssubs=0&page="
    )
    url = None
    for i in range(1, 51):
        webpage = main_webpage + str(i)
        if webpage not in loaded:
            url = webpage
            break

    if not url:
        with Path("toomany.txt").open("a", encoding="utf-8") as f:
            f.write(main_webpage[:-6] + "\n")
        suburbs.pop(suburb)
        continue

    date_val = str(suburbs[suburb])
    year = date_val[0:4]
    month = date_val[4:6]
    day = date_val[6:8]
    print(f"{day}/{month}/{year} : {suburb: <30} - {url}")

    driver.get(url)
    if "The requested URL was not found on the server." in driver.page_source:
        print("URL not found: " + url)
        msg = f"URL not found: {url}"
        raise RuntimeError(msg)
    if "No exact matches" in driver.page_source:
        if "page=1" in url:
            print("No properties in suburb: " + url)
            with finished_suburbs_file.open("a", encoding="utf-8") as f:
                f.write(suburb + "\n")
            suburbs.pop(suburb)
            continue
        with finished_suburbs_file.open("a", encoding="utf-8") as f:
            f.write(suburb + "\n")
        suburbs.pop(suburb)
    else:
        property_dictionary = html_to_dict(driver.page_source)
        for value in property_dictionary.values():
            if str(value["id"]) in ids:
                continue
            ids.add(str(value["id"]))
            row = value_to_row(value)
            if row[6] != "":
                date = float(row[6])
                if row[8] not in suburbs or date < suburbs[row[8]]:
                    suburbs[row[8]] = date
            with Path("all.csv").open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(row)
        if len(property_dictionary.values()) < PAGE_SIZE_LIMIT:
            with finished_suburbs_file.open("a", encoding="utf-8") as f:
                f.write(suburb + "\n")
            suburbs.pop(suburb)

    loaded.add(url)
    with loaded_file.open("a", encoding="utf-8") as f:
        f.write(url + "\n")
