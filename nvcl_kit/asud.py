"""
Retrieves stratigraphy data from the "Australian Stratigraphic Units Database"

Ref:
"Geoscience Australia and Australian Stratigraphy Commission. (2017). Australian Stratigraphic Units Database."

https://www.ga.gov.au/data-pubs/datastandards/stratigraphic-units
"""

import sys
import geojson
import logging
from requests import post, RequestException
import json
from pyproj import Transformer
from owslib.wms import WebMapService
from owslib.util import ServiceException
from http.client import HTTPException


GA_SURF_GEO_WMS = "http://services.ga.gov.au/gis/services/GA_Surface_Geology/MapServer/WmsServer"
""" Geoscience Australia Surface Geology WMS Service
    https://data.gov.au/data/dataset/48fe9c9d-2f10-49d2-bd24-ac546662c4ec
"""

GSUD_API = "https://api.asud.ga.gov.au/api"
""" API URL for 'Australian Stratigraphic Units Database'
"""

WMS_CRS = "EPSG:3857"
""" WMS CRS
"""

WMS_LAYER_NAME = "AUS_GA_1M_GUPoly_Lithostratigraphy"
""" WMS Layer Name
"""

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
    FORMATTER = logging.Formatter('%(name)s -- %(levelname)s - %(message)s')

    # Add formatter to ch
    HANDLER.setFormatter(FORMATTER)

    # Add handler to LOGGER and set level
    LOGGER.addHandler(HANDLER)


def _get_asud_strat_no(lon, lat):
    ''' Retrieves the stratigraphy number from the ASUD given latitude & longitude (EPSG:4326)

    :param lon: longitude, float
    :param lat: latitude, float

    :returns: stratigraphy number (string) from ASUD as a string or None upon error or not found
    '''
    # Convert lat/lon EPSG:4326 to EPSG:3857
    transformer = Transformer.from_crs("EPSG:4326", WMS_CRS, always_xy=True)
    bb_x, bb_y = transformer.transform(lon, lat)

    # Connect to WMS service
    try:
        wms = WebMapService(url=GA_SURF_GEO_WMS, version='1.3.0')
    except Exception as exc:
        LOGGER.warning("Cannot connect to WMS service: %s", str(exc))
        return None

    resp = None

    # Look for geojson as a response format
    for info_format in wms.getOperationByName('GetFeatureInfo').formatOptions:
        if info_format == 'application/geojson':
            try:
                # Sent a request
                bb_sz = 10
                resp = wms.getfeatureinfo(
                              layers=[WMS_LAYER_NAME],
                              srs=WMS_CRS,
                              bbox=(bb_x-bb_sz, bb_y-bb_sz, bb_x+bb_sz, bb_y+bb_sz),
                              size=(1254, 318),
                              format='image/jpeg',
                              query_layers=[WMS_LAYER_NAME],
                              info_format=info_format,
                              xy=(789, 128))
            except (RequestException, HTTPException, ServiceException, OSError) as exc:
                LOGGER.warning("WMS getfeatureinfo exception: %s", str(exc))
                return None
            break
    # If valid request, parse the geojson response
    if resp is not None:
        try:
            featureColl = geojson.loads(resp.read())
        except json.decoder.JSONDecodeError as exc:
            LOGGER.warning("Error decoding geojson: %s", str(exc))
            return None

        # Fetch the stratigraphy number
        try:
            strat_no = featureColl["features"][0]["properties"]["stratno"]
        except(IndexError, KeyError):
            # Not found
            LOGGER.debug("Could not find stratigraphy number")
            return None
        return strat_no

    LOGGER.warning("Could not find geojson in WMS getcapabilities")
    return None


def get_asud_record(lon, lat):
    ''' Retrieves a stratigraphy record from the 'Australian Strategraphic Units Database'

    :param lon: longitude (float or string)
    :param lat: latitude (float or string)

    :returns: stratigraphy record as a dict or None upon error or not found
    '''
    # Check input parameters
    if not isinstance(lon, float):
        try:
            lon_flt = float(lon)
        except (ValueError, TypeError):
            LOGGER.warning("lon parameter is not a float")
            return None
    else:
        lon_flt = lon

    if not isinstance(lat, float):
        try:
            lat_flt = float(lat)
        except (ValueError, TypeError):
            LOGGER.warning("lat parameter is not a float")
            return None
    else:
        lat_flt = lat

    strat_no = _get_asud_strat_no(lon_flt, lat_flt)
    if strat_no is not None:
        try:
            resp = post(GSUD_API, data=json.dumps({"actionName": "searchStratigraphicUnitsDetails", "stratNo": strat_no}))
        except RequestException as exc:
            LOGGER.error("Error querying Stratigraphic Units DB: %s", str(exc))
            jresp = {"response": None}
        else:
            try:
                jresp = json.loads(resp.text)
            except json.decoder.JSONDecodeError as exc:
                LOGGER.warning("Error decoding ASUD json response: %s", str(exc))
                jresp = {"response": None}
        return jresp.get("response")
    return None


#if __name__ == "__main__":
#    print(get_asud_record(140.625, -31.353637))
