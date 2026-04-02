import sys
import logging
from urllib3.util import Retry

from shapely import LinearRing, MultiPolygon, Polygon
import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import HTTPError

from nvcl_kit.constants import HTTP_RETRY_CODES, NUM_RETRIES, BACKOFF_FACTOR

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

def make_cql_filter(bbox: dict, poly: Polygon|MultiPolygon|LinearRing, poly_srid: int = 4326, remove_rings: bool = False) -> str:
    """Generates a CQL filter string for filtering boreholes by bounding box or polygon. If both bbox and poly are provided, bbox will be used.

    Args:
        bbox (dict): Bounding box with keys 'west', 'south', 'east', 'north' in EPSG:4326
        poly (Polygon | MultiPolygon | LinearRing): Shapely Polygon, MultiPolygon, or LinearRing geometry
        poly_srid (int, optional): SRID for the polygon geometry. Defaults to 4326.
        remove_rings (bool, optional): Whether to remove interior rings from the polygon. Defaults to False.

    Returns:
        str: CQL filter string
    """
    if bbox is not None:
        return f"BBOX(shape, {bbox['west']}, {bbox['south']}, {bbox['east']}, {bbox['north']}) and nvclCollection = 'true'"
    elif poly is not None:
        if remove_rings and isinstance(poly, Polygon):
            poly = Polygon(poly.exterior)
        elif remove_rings and isinstance(poly, MultiPolygon):
            poly = MultiPolygon([Polygon(p.exterior) for p in poly.geoms])
        
        if isinstance(poly, LinearRing):
            poly = Polygon(poly)

        srid = f"SRID={poly_srid};" if poly_srid else ""
        return f"Within(shape, {srid}{poly.wkt}) and nvclCollection = 'true'"
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
            retries = Retry(total=NUM_RETRIES,
                            backoff_factor=BACKOFF_FACTOR,
                            status_forcelist=HTTP_RETRY_CODES,
                            allowed_methods=["GET"]
                           )
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # Sending the request
            LOGGER.debug(f"Sending {url=} {params=}")
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
