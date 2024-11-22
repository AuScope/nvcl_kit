from shapely import Polygon
import requests
import sys
import logging
import json

LOG_LVL = logging.INFO
''' Initialise debug level, set to 'logging.INFO' or 'logging.DEBUG'
'''

# Set up debugging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOG_LVL)

if not LOGGER.hasHandlers():

    # Create logging console handler
    HANDLER = logging.StreamHandler(sys.stdout)

    # Create logging formatter
    FORMATTER = logging.Formatter('%(name)s -- %(levelname)s - %(funcName)s: %(message)s')

    # Add formatter to ch
    HANDLER.setFormatter(FORMATTER)

    # Add handler to LOGGER and set level
    LOGGER.addHandler(HANDLER)

def make_cql_filter(bbox: dict, poly: Polygon) -> str:
    if bbox is not None:
        return f"BBOX(shape, {bbox['west']}, {bbox['south']}, {bbox['east']}, {bbox['north']}) and nvclCollection = 'true'"
    elif poly is not None:
        # Example: "Within(shape, POLYGON((-35.2438 147.8011, -35.0684 147.8011, -35.0684 147.9966, -35.2438 147.9966, -35.2438 147.8011))) and nvclCollection = 'true'"
        poly_str = "Within(shape, POLYGON(("
        for y,x in poly.exterior.coords:
            poly_str += f"{y} {x},"
        return poly_str.rstrip(",") + "))) and nvclCollection = 'true'"
    else:
        return "nvclCollection = 'true'"

def is_all_nvcl(features):
    """
    Test for all NVCL boreholes
    """
    for feature in features:
        try:
            assert(feature['properties']['nvclCollection'] == 'true')
        except:
            print("FAIL - Not all NVCL!!")
            return
        print("PASS - all NVCL")

def make_cql_request(url: str, prov: str, cql_filter: str, max_features: int):
    # Parameters for the GetFeature request
    params = {
              "service": "WFS",
              "version": "1.1.0",
              "request": "GetFeature",
              "typename": "gsmlp:BoreholeView",
              "outputFormat": "json",
              "CQL_FILTER": cql_filter,
              "maxFeatures": str(max_features)
             }

    # Sending the request
    try:
        response = requests.get(url, params=params)
    except requests.RequestException as re:
        LOGGER.error(f"{prov} returned error sending WFS GetFeature: {re}")
        return []

    # Check if the request was successful
    if response.status_code == 200:
        try:
            resp = response.json()
        except requests.JSONDecodeError as jde:
            LOGGER.error(f"Error parsing JSON from {prov} WFS GetFeature response: {jde}")
            return []
        return resp['features']
    LOGGER.error(f"{prov} returned error {response.status_code} in WFS GetFeature response: {response.text}")
    return []
