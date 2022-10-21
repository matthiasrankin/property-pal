"""
Functions relating to conversion of html data to
flattened dictionaries which may be used with
pandas.DataFrame(). See scripts/pull_property_data.
"""

import json
import re
import time

from bs4 import BeautifulSoup


def parse_cost(cost_string):
    """
    Helper function to parse cost strings in
    property payload.
    """
    cost_string = cost_string.split("£")[1]
    cost_string = cost_string.split("pa")[0]
    cost_string = cost_string.replace(",", "")
    cost_string = cost_string.strip()
    
    return float(cost_string)


def parse_size(size_string):
    """
    Helper function to parse size strings in
    property payload.
    """
    size_string = size_string.replace(",", "")

    if "metres" in size_string:
        size_string = size_string.split("sq. metres")[0]
        size_string = size_string.strip()
        size_in_sq_metres = float(size_string)

    elif "feet" in size_string:
        size_string = size_string.split("sq. feet")[0]
        size_string = size_string.strip()
        size_in_sq_feet = float(size_string)
        size_in_sq_metres = size_in_sq_feet * 0.092903
    
    return size_in_sq_metres


def extract_key_info(property_dict):
    """
    Helper function to extract rates, stamp duty,
    and property size information from property
    payload.
    """
    try:
        key_info = property_dict["keyInfo"]
    except KeyError:
        return {}
    
    output_dict = {}
    
    for info in key_info:
        if info["name"] == "Rates":
            output_dict["rates_per_annum"] = parse_cost(info["text"])
        if info["name"] == "Stamp Duty":
            output_dict["stamp_duty_first_time_buyer"] = parse_cost(info["buyerTypeCosts"]["FIRST_TIME_BUYER"])
            output_dict["stamp_duty_home_mover"] = parse_cost(info["buyerTypeCosts"]["HOME_MOVER"])
            output_dict["stamp_duty_buy_to_let"] = parse_cost(info["buyerTypeCosts"]["BUY_TO_LET_INVESTOR"])
            output_dict["stamp_duty_additional_home"] = parse_cost(info["buyerTypeCosts"]["ADDITIONAL_HOME_BUYER"])
        if info["name"] == "Size":
            output_dict["size"] = parse_size(info["text"])
            
    return output_dict


def clean_text_description(property_dict):
    """
    Function to perform basic cleaning on
    text description for a given property.
    
    Parameters:
    -----------
    property_dict: dict
    
    Returns:
    --------
    String contained slightly cleaned description
    of property.
    """

    try:
        description = property_dict["description"]
    except KeyError:
        return ""

    description = (BeautifulSoup(description, features="lxml")
                   .get_text()
                   .replace('\xa015', '')
                   .replace('\xa0', ''))

    description = re.sub(r'(?<=[a-z])(?=[A-Z])', '\n', description)

    return description


def flatten_property(property_dict, page_type=None):
    """
    Extract desired information about a given property
    and place into a flattened dict. Called by
    convert_html().
    
    Parameters:
    -----------
    property_dict: dict
    
    page_type: str
        Either "search" or "property".
    
    Returns:
    --------
    A list containing a flattened dict containing
    information of interest about the property.
    """

    def get_image_urls(property_dict):
        """
        Returns list of image urls for a given property.
        """

        image_urls = []
        try:
            for image in property_dict["images"]:
                image_urls.append(image["url"])
        except KeyError:
            pass

        return image_urls
    
    def nested_get(property_dict, key_1, key_2, default=""):
        """
        Function to handle default values for nested
        data.
        """
        
        try:
            tmp = property_dict.get(key_1)
            value = tmp.get(key_2, default)
        except (KeyError, AttributeError):
            value = default

        return value

    if page_type not in ["search", "property"]:
        raise ValueError(
            "`page_type` must be either `search` or `property`. "
            f"Got {page_type}."
        )

    property_rows = []

    if page_type == "search":
        property_info = {
            "id": property_dict.get("id", ""),
            "path_id": property_dict.get("pathId", ""),
            "property_url": property_dict.get("shareURL", None),
        }

        if property_dict.get("history"):
            for update in property_dict["history"]:
                property_instance = property_info.copy()
                property_instance.update({
                    "price": update.get("price", "POA"),
                    "price_difference": update["difference"],
                    "price_percentage_difference": update["differencePercentage"],
                    "status": update["status"]["key"],
                    "time_modified": update["timeModified"]
                })
                property_rows.append(property_instance)
        else:
            property_rows.append(property_info)

    elif page_type == "property":

        property_info = {
            "id": property_dict.get("id", ""),
            "path_id": property_dict.get("pathId", ""),
            "property_url": property_dict.get("shareURL", None),
            "name": property_dict.get("name", ""),
            "address": property_dict.get("displayAddress", ""),
            "building_name": property_dict.get("buildingName", ""),
            "house_number": property_dict.get("houseNumber", ""),
            "street": property_dict.get("street", "") ,
            "address_line_1": property_dict.get("addressLine1", ""),
            "address_line_2": property_dict.get("addressLine2", ""),
            "town": property_dict.get("town", ""),
            "region": property_dict.get("region", ""),
            "postcode": property_dict.get("postcode", ""),
            "country_code": property_dict.get("countryCode", ""),
            "latitude": nested_get(property_dict, "coordinate", "latitude"),
            "longitude": nested_get(property_dict, "coordinate", "longitude"),
            "min_price": nested_get(property_dict, "price", "minPrice"),
            "max_price": nested_get(property_dict, "price", "maxPrice"),
            "price": nested_get(property_dict, "price", "price"),
            "property_type": nested_get(property_dict, "propertyType", "key"),
            "property_style": nested_get(property_dict, "style", "key"),
            "furnished_type": property_dict.get("furnishedType", ""),
            "num_bedrooms": property_dict.get("numBedrooms", ""),
            "num_bathrooms": property_dict.get("numBathrooms", ""),
            "num_reception_rooms": property_dict.get("numReceptionRooms", ""),
            "sale_type": nested_get(property_dict, "saleType", "key"),
            "epc_rating": nested_get(property_dict, "epc", "ratingShorthand"),
            "co2_rating": nested_get(
                property_dict, "epc", "co2RatingShorthand"),
            "organisation": nested_get(
                property_dict, "account", "organisation"),
            "developer": nested_get(property_dict, "account", "developer"),
            "agent": nested_get(property_dict, "account", "organisation"),
            "development_status": nested_get(
                property_dict, "developmentStatus", "key"),
            "text_description": property_dict["briefText"],
            "description": clean_text_description(property_dict),
            "images": get_image_urls(property_dict),
            "first_posted": property_dict.get("activationTime", ""),
            "last_updated": property_dict.get("listingUpdatedTime", ""),
        }

#         property_info["latitude"] = nested_get(property_dict, "coordinate", "latitude")
#         property_info["longitude"] = nested_get(property_dict, "coordinate", "longitude")
#         property_info["property_type"] = nested_get(property_dict, "propertyType", "key")
#         property_info["property_style"] = nested_get(property_dict, "style", "key")
#         property_info["sale_type"] = nested_get(property_dict, "saleType", "key"),
#         property_info["epc_rating"] = nested_get(property_dict, "epc", "ratingShorthand")
#         property_info["co2_rating"] = nested_get(property_dict, "epc", "co2RatingShorthand")
#         property_info["organisation"] = nested_get(property_dict, "account", "organisation")
#         property_info["developer"] = nested_get(property_dict, "account", "developer")
#         property_info["agent"] = nested_get(property_dict, "account", "organisation")
#         property_info["development_status"] = nested_get(
#             property_dict, "developmentStatus", "key"
#         )

#         property_info["min_price"] = nested_get(property_dict, "price", "minPrice")
#         property_info["max_price"] = nested_get(property_dict, "price", "maxPrice")
#         property_info["price"] = nested_get(property_dict, "price", "price")

        property_info.update(extract_key_info(property_dict))
        property_rows.append(property_info)

    return property_rows


def convert_html(soup, page_type="search"):
    """
    Function to convert scraped html into a list of dicts
    which can be converted directly into a pandas.DataFrame.
    
    Parameters:
    -----------
    html_text: str
        Either directly scraped, or read in from json. If scraped,
        should be like requests.get().text. If read in, should be
        read from `PROJECT_DIRECTORY/data/html/html.json`.
        
    page_type: str
        Default is "search", for converting data scraped from the
        general results page. Change to "property" to convert data
        scraped from an individual property's page.
        
    Returns:
    --------
    List of dictionaries, with each instance corresponding to
    an updated instance of a property listing.
    """

    if page_type not in ["search", "property"]:
        raise ValueError(
            "`page_type` must be either `search` or `property`. "
            f"Got {page_type}."
        )

    script_tags = soup.findAll("script")

    json_data = []

    for tag in script_tags:
        try:
            if tag["type"] == "application/json":
                json_data.append(tag.text)
            else:
                continue
        except KeyError:
            pass

    for script_string in json_data:
        try:
            properties = json.loads(script_string)
        except:
            continue

    converted_properties = []

    if page_type == "search":
        for property_dict in properties['props']['pageProps']['initialState']['properties']['data']['results']:
            converted_properties.extend(
                flatten_property(property_dict, page_type=page_type)
            )

    elif page_type == "property":
        
        property_dict = properties["props"]["pageProps"]["property"]
        converted_properties.extend(
            flatten_property(property_dict, page_type=page_type)
        )

    return converted_properties
