"""
Utility functions for the Domain web scrapers.
Contains shared logic for HTML parsing and data transformation.
"""

import json
from datetime import UTC, datetime
from typing import Any


def add_column(group: dict[str, Any], header: str) -> str:
    """Returns '' if the key 'header' does not excist in dict 'group'."""
    val = group.get(header, "")
    return str(val) if val is not None else ""


def html_to_dict(s: str) -> dict[str, Any]:
    """Converts a domain.com.au search to a list of property information."""
    search = '"listingsMap":'
    start_index = s.find(search)
    if start_index == -1:
        return {}
    start_index += len(search)
    end_index = start_index
    count = 0
    while end_index < len(s):
        if s[end_index] == "{":
            count += 1
        elif s[end_index] == "}":
            count += -1
        if count == 0:
            break
        end_index += 1
    try:
        return json.loads(s[start_index : end_index + 1])
    except json.JSONDecodeError:
        return {}


def value_to_row(value: dict[str, Any]) -> list[Any]:
    """Converts property dictionary to a list of values for CSV."""
    row = []
    row.append(value["id"])
    row.append(value["listingType"])
    row.append(value["listingModel"]["url"])
    row.append(value["listingModel"]["price"])
    if row[-1] == "Price Withheld":
        row[-1] = ""
    elif isinstance(row[-1], str) and row[-1].startswith("$"):
        row[-1] = row[-1][1:].replace(",", "")

    row.append(value["listingModel"]["tags"]["tagClassName"])
    row.append(value["listingModel"]["tags"]["tagText"])
    try:
        date_str = " ".join(row[-1].split()[-3:])
        date = datetime.strptime(date_str, "%d %b %Y").replace(tzinfo=UTC)
        row.append(date.strftime("%Y%m%d"))
    except ValueError, IndexError:
        row.append("")

    address = value["listingModel"]["address"]
    row.append(add_column(address, "street").replace("\n", " "))
    row.append(add_column(address, "suburb"))
    row.append(add_column(address, "state"))
    row.append(add_column(address, "postcode"))
    row.append(add_column(address, "lat"))
    row.append(add_column(address, "lng"))

    features = value["listingModel"]["features"]
    row.append(add_column(features, "beds"))
    row.append(add_column(features, "baths"))
    row.append(add_column(features, "parking"))
    row.append(add_column(features, "propertyType"))
    row.append(add_column(features, "propertyTypeFormatted"))
    row.append(add_column(features, "isRural"))
    row.append(add_column(features, "landSize"))
    row.append(add_column(features, "landUnit"))
    if row[-1] == "m²":
        row[-1] = "m2"
    row.append(add_column(features, "isRetirement"))
    return row
