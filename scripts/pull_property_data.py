"""
Script to scrape, convert and save property data from 
https://www.propertypal.com/property-for-sale/northern-ireland.
"""

import datetime
import json
import requests
import sys
import time

import pandas as pd

from bs4 import BeautifulSoup

sys.path.append(
    os.path.join(sys.path[0].split("property-pal")[0], "property-pal")
)

from property_pal import PROJECT_DIRECTORY
from property_pal.conversion import convert_html
from property_pal.scraping import (
    get_new_development_urls,
    save_raw_html,
    scrape_html
)

HTML_PATH = PROJECT_DIRECTORY / "data" / "html" / "html.json"
HEADERS_PATH = PROJECT_DIRECTORY / "tokens" / "headers.json"
PROPERTIES_PATH = PROJECT_DIRECTORY / "data" / "properties" / "properties.csv"

with open(HEADERS_PATH, "r", encoding="utf-8") as file_path:
    HEADERS = json.load(file_path)

url = "https://www.propertypal.com/property-for-sale/northern-ireland"

if __name__ == "__main__":

    start_time = time.time()
    date_string = datetime.datetime.today().strftime(format='%y-%m-%d')

    status_code = "200"
    page_number = 1
    keep_attempting = True
    try:
        properties_df = pd.read_csv(PROPERTIES_PATH)
    except FileNotFoundError:
        properties_df = pd.DataFrame([])

    print("Starting scrape:\n")

    while (status_code == "200" and keep_attempting):

        print(f"Page Number: {page_number}")
        print(f"URL: {url}")

        html, status_code = scrape_html(url=url, headers=HEADERS)

        soup = BeautifulSoup(html.text, 'lxml')

        try:
            rows = convert_html(soup)

            new_property_urls = {i["property_url"] for i in rows}

            property_rows = []
            for new_property_url in new_property_urls:
                property_html, property_status_code = scrape_html(
                    url=new_property_url, headers=HEADERS
                )
                property_soup = BeautifulSoup(property_html.text, 'lxml')

                new_dev_urls = get_new_development_urls(property_soup)

                if len(new_dev_urls) > 0:
                    for new_dev_url in new_dev_urls:
                        new_dev_html, new_dev_status = scrape_html(
                            url=new_dev_url, headers=HEADERS
                        )

                        new_dev_soup = BeautifulSoup(new_dev_html.text, 'xml')
                        property_rows.extend(
                            convert_html(new_dev_soup, page_type="property")
                        )

                else:
                    property_rows.extend(
                        convert_html(property_soup, page_type="property")
                    )

            search_page_df = pd.DataFrame(rows)
            property_pages_df = pd.DataFrame(property_rows)

            join_cols = ["id", "path_id", "property_url"]

            tmp_properties_df = pd.merge(
                search_page_df, property_pages_df, how="outer", on=join_cols
            )

            tmp_properties_df["last_pull_date"] = date_string

            properties_df = pd.concat([properties_df, tmp_properties_df], sort=True)

        except Exception as e:
            print(e)
            save_raw_html(html.text, page_number, HTML_PATH)

        next_button = soup.find("link", {"rel": "next"}, href=True)
        if next_button is None:
            keep_attempting = False
            break

        url = next_button["href"]
        page_number += 1

    print("Finished scraping. Writing to CSV.")

    properties_df.to_csv(PROPERTIES_PATH, index=False)

    wall_time = time.time() - start_time

    print(f"Finished. Total time: {wall_time}")
