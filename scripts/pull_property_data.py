"""
Script to scrape, convert and save property data from 
https://www.propertypal.com/property-for-sale/northern-ireland.
"""

import json
import requests
import sys
import time

import pandas as pd

from bs4 import BeautifulSoup


sys.path.append("C:\\Users\\Matthew\\Documents\\Allstate\\PLB\\property_pal")

from property_pal import PROJECT_DIRECTORY
from property_pal.conversion import convert_html
from property_pal.scraping import save_raw_html, scrape_html

HTML_PATH = PROJECT_DIRECTORY / "data" / "html" / "html.json"
HEADERS_PATH = PROJECT_DIRECTORY / "tokens" / "headers.json"
PROPERTIES_PATH = PROJECT_DIRECTORY / "data" / "properties" / "properties.csv"

with open(HEADERS_PATH, "r", encoding="utf-8") as file_path:
    HEADERS = json.load(file_path)

URL = "https://www.propertypal.com/property-for-sale/northern-ireland"

if __name__ == "__main__":
    
    status_code = "200"
    page_number = 0
    keep_attempting = True
    try:
        properties_df = pd.read_csv(PROPERTIES_PATH)
    except FileNotFoundError:
        properties_df = pd.DataFrame([])

    while (status_code == "200" and keep_attempting):
        
        print(f"Page Number: {page_number}")

        html, status_code = scrape_html(url=URL, headers=HEADERS)
        
        soup = BeautifulSoup(html.text, 'lxml')

        try:
            rows = convert_html(soup)

            new_property_urls = {i["property_url"] for i in rows}

            property_rows = []
            for url in new_property_urls:
                property_html, property_status_code = scrape_html(
                    url=url, headers=HEADERS
                )
                property_soup = BeautifulSoup(property_html.text, 'lxml')
                property_rows.extend(convert_html(property_soup, page_type="property"))

            search_page_df = pd.DataFrame(rows)
            property_pages_df = pd.DataFrame(property_rows)

            tmp_properties_df = pd.merge(
                search_page_df, property_pages_df, how="outer", on="id"
            )

            properties_df = pd.concat([properties_df, tmp_properties_df])

        except Exception as e:
            print(e)
            break
            save_raw_html(html.text, page_number, HTML_PATH)

        next_button = soup.find("link", {"rel": "next"}, href=True)
        if next_button is None:
            keep_attempting = False
            break

        url = next_button["href"]
        page_number += 1
        
    properties_df.to_csv(PROPERTIES_PATH, index=False)
