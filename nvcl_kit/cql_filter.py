import sys
import logging
import json
from urllib3.util import Retry

from shapely import Polygon
import requests
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.exceptions import HTTPError

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

def make_cql_request(url: str, prov: str, cql_filter: str, max_features: int):
    """
    Makes an OGC WFS GetFeature v1.1.0 request using GET and expecting a JSON response
    Caller can supply a CQL filter

    :param url: OGC WFS URL
    :param prov: provider e.g. 'nsw'
    :param cql_filter: CQL filter string e.g. filter by polygon
    :param max_features: maximum number of features to return, if < 1 then all boreholes are returned
    :returns: list of features, each feature is a dict
    """
    # NB: Does not perform WFS request paging, may be required in future

    # Parameters for the GetFeature request
    params = {
              "service": "WFS",
              "version": "1.1.0",
              "request": "GetFeature",
              "typename": "gsmlp:BoreholeView",
              "outputFormat": "json",
              "CQL_FILTER": cql_filter
             }
    if max_features > 0:
        params["maxFeatures"] = str(max_features)

    try:
        with requests.Session() as s:

            # Retry with backoff
            retries = Retry(total=5,
                            backoff_factor=0.5,
                            status_forcelist=[429, 502, 503, 504]
                           )
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # Sending the request
            response = s.get(url, params=params)
    except (HTTPError, requests.RequestException) as e:
        LOGGER.error(f"{prov} returned error sending WFS GetFeature: {e}")
        return []

    # Check if the request was successful
    if response.status_code == 200:
        try:
            resp = response.json()
        except (TypeError, requests.JSONDecodeError) as e:
            LOGGER.error(f"Error parsing JSON from {prov} WFS GetFeature response: {e}")
            return []
        return resp['features']
    LOGGER.error(f"{prov} returned error {response.status_code} in WFS GetFeature response: {response.text}")
    return []
