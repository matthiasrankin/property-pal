"""
Functions relating to the scraping of html data 
from the web for subsequent conversion into
a dataframe. See scripts/pull_property_data.
"""

import json
import requests
import time

from bs4 import BeautifulSoup

from property_pal import PROJECT_DIRECTORY


def save_raw_html(html, page_number, html_path):
    """
    Saves raw html text to html_folder for conversion
    later.
    
    Parameters:
    -----------
    html: str
        Like the output of `requests.get().text`.
        
    page_number: int
        Defined in `scrape_html` - used to organise html
        data.
        
    html_dir: str, pathlib.WindowsPath, or similar
        Directory in which to store html.
    """
    page_number = str(page_number)
    try:
        with open(html_path, "r", encoding="utf-8") as file_path:
            html_dict = json.load(file_path)
    except FileNotFoundError:
        html_dict = {}
        
    html_dict.update({page_number: html})
    
    with open(html_path, "w") as fp:
        json.dump(html_dict, fp)
        

def scrape_html(url, headers=None):

    if headers is None:
        raise ValueError(
            'Please supply `headers`. This should be a dict'
            'with keys "Accept-Language" and "User-Agent".'
            'See http://myhttpheader.com/ for help.'
        )        

    
    data = requests.get(url, headers=headers)
    status_code = str(data.status_code)
    
    return data, status_code


def pull(url, headers, page_type):
    
    status_code = "200"
    page_number = 0
    keep_attempting = True

    while (status_code == "200"
           and keep_attempting):

        html, status_code = scrape_html(url, headers)

        soup = BeautifulSoup(html.text, 'lxml')

        try:
            rows = convert_html(soup, page_type=page_type)
        except:
            save_raw_html(html.text, page_number, html_path)

        next_button = soup.find("link", {"rel": "next"}, href=True)
        if next_button is None:
            keep_attempting = False
            break

            url = next_button["href"]
            page_number += 1

        
# def scrape_html_old(url, headers=None, html_path=HTML_PATH):
    
#     if headers is None:
#         raise ValueError(
#             'Please supply `headers`. This should be a dict'
#             'with keys "Accept-Language" and "User-Agent".'
#             'See http://myhttpheader.com/ for help.'
#         )        

#     status_code = "200"
#     page_number = 0
#     keep_attempting = True

#     while (status_code == "200"
#            and keep_attempting):

#         data = requests.get(url, headers=headers)
#         status_code = str(data.status_code)

#         save_raw_html(data.text, page_number, html_path)

#         soup = BeautifulSoup(data.text, 'lxml')

#         next_button = soup.find("link", {"rel": "next"}, href=True)

#         if next_button is None:
#             keep_attempting = False
#             break

#         url = next_button["href"]
#         page_number += 1

#         time.sleep(2)
