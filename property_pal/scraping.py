"""
Functions relating to the scraping of html data 
from the web for subsequent conversion into
a dataframe. See scripts/pull_property_data.
"""

import json
import requests
import time

from bs4 import BeautifulSoup


def save_raw_html(html, page_number, html_path):
    """
    Saves raw HTML text to html_path for conversion
    later.
    
    Parameters:
    -----------
    html: str
        Like the output of `requests.get().text`.
        
    page_number: int
        Defined in `scrape_html` - used to organise html
        data.
        
    html_path: str, pathlib.WindowsPath, or similar
        Directory in which to store html.
    
    Effects:
    --------
    Writes HTML code to a dictionary stored in `html_path`,
    where keys are the `page_number`.
    """

    page_number = str(page_number)
    try:
        with open(html_path, "r", encoding="utf-8") as file_path:
            html_dict = json.load(file_path)
    except FileNotFoundError:
        html_dict = {}

    html_dict.update({page_number: html})

    with open(html_path, "w") as file_path:
        json.dump(html_dict, file_path)


def scrape_html(url, headers=None):
    """
    Function to scrape data from `url` via a
    get request.

    Parameters:
    -----------
    url: str
        URL for website to be scraped.

    headers: dict
        Dictionary with keys "Accept-Language" and "User-Agent". 
        See http://myhttpheader.com/ for help.

    Returns:
    --------
    data: Output of requests.get().
        HTML code stored in data.text.

    status_code: str
        Status code of get request. Successful requests have
        status_code = 200.

    """

    if headers is None:
        raise ValueError(
            'Please supply `headers`. This should be a dict'
            'with keys "Accept-Language" and "User-Agent".'
            'See http://myhttpheader.com/ for help.'
        )

    data = requests.get(url, headers=headers)
    status_code = str(data.status_code)

    return data, status_code


def get_new_development_urls(soup):
    """
    Function to get URLS for individual
    properties listed in new development pages.
    
    Parameters:
    -----------
    soup: bs4.BeautifulSoup
        Obtained from scraping the new development page.
        
    Returns:
    --------
    List of URLS for developed properties.
    """

    urls = []
    href_list = soup.find_all("a", href=True)

    for i in href_list:
        if i.find("strong") is not None:
            urls.append(f"https://www.propertypal.com{i['href']}")
    
    return urls
