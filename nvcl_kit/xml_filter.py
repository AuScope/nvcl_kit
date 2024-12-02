import sys
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib3.exceptions import HTTPError
from urllib3.util import Retry

from shapely import Polygon
import requests
from requests import Session
from requests.adapters import HTTPAdapter

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

def pretty_print(xml_str):
    print(minidom.parseString(xml_str).toprettyxml(indent="   "))

def make_polygon_prop(coords: str) -> str:
    intersects = ET.Element("ogc:Intersects")
    intersects.set("xmlns:ogc","http://www.opengis.net/ogc")
    intersects.set("xmlns:gml","http://www.opengis.net/gml")
    intersects.set("xmlns:gsmlp","http://xmlns.geosciml.org/geosciml-portrayal/4.0")

    propertyName = ET.SubElement(intersects, "ogc:PropertyName")
    propertyName.text = "shape"
    multiPolygon = ET.SubElement(intersects, "gml:MultiPolygon")
    multiPolygon.set("srsName", "urn:ogc:def:crs:EPSG::4326")
    polygonMember = ET.SubElement(multiPolygon, "gml:polygonMember")

    polygon = ET.SubElement(polygonMember, "gml:Polygon")
    polygon.set("srsName", "EPSG:4326")

    outerBoundaryIs = ET.SubElement(polygon, "gml:outerBoundaryIs")
    linearRing = ET.SubElement(outerBoundaryIs, "gml:LinearRing")

    coordinates = ET.SubElement(linearRing, "gml:coordinates")
    coordinates.set("xmlns:gml", "http://www.opengis.net/gml")
    coordinates.set("decimal", ".")
    coordinates.set("cs" ,",")
    coordinates.set("ts", " ")
    coordinates.text = coords

    xml_str = ET.tostring(intersects, encoding='unicode')
    return xml_str

def make_nvcl_like_filter():
    """
    This works for all services, using 'PropertyIsLike' because "PropertyIsEqualTo" does not work for NT
    """
    xml_filter ="""<ogc:Filter xmlns:gsmlp="http://xmlns.geosciml.org/geosciml-portrayal/4.0"
                               xmlns:ogc="http://www.opengis.net/ogc">
                        <ogc:PropertyIsLike wildCard="%" singleChar="#" escapeChar="!">
                            <ogc:PropertyName>gsmlp:nvclCollection</ogc:PropertyName>
                            <ogc:Literal>true</ogc:Literal>
                        </ogc:PropertyIsLike>
                   </ogc:Filter>"""
    return xml_filter

def make_nvcl_like_prop():
    xml_filter ="""<ogc:PropertyIsLike xmlns:ogc="http://www.opengis.net/ogc" xmlns:gsmlp="http://xmlns.geosciml.org/geosciml-portrayal/4.0" wildCard="%" singleChar="#" escapeChar="!">
                       <ogc:PropertyName>gsmlp:nvclCollection</ogc:PropertyName>
                       <ogc:Literal>true</ogc:Literal>
                   </ogc:PropertyIsLike>"""
    return xml_filter

def make_xml_request(url: str, prov: str, xml_filter: str, max_features: int):
    """
    Makes an OGC WFS GetFeature v1.0.0 request using POST and expecting a JSON response
    """
    data = { "service": "WFS",
             "filter": xml_filter,
             "version": "1.0.0",
             "request": "GetFeature",
             "typeName": "gsmlp:BoreholeView",
             "outputFormat": "json",
             "resultType": "results",
             # NT is misconfigured and returns no features if 'maxFeatures' is used
             # "maxFeatures": str(max_features) 
           }
    # Send the POST request with the XML payload 
    try:
        with requests.Session() as s:

            # Retry with backoff
            retries = Retry(total=5,
                            backoff_factor=0.5,
                            status_forcelist=[429, 502, 503, 504]
                           )
            s.mount('https://', HTTPAdapter(max_retries=retries))

            # Sending the request
            response = s.post(url, data=data)
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


def make_poly_coords(bbox: dict, poly: Polygon) -> str:
    """
    Converts a bounding box dict to polygon coordinate string
    """
    poly_str = ""
    if bbox is not None:
        # According to epsg.io's OCG WKT 2 definition, EPSG:4326 is lat,long order
        poly_str = f"{bbox['south']},{bbox['west']} {bbox['north']},{bbox['west']} {bbox['north']},{bbox['east']} {bbox['south']},{bbox['east']} {bbox['south']},{bbox['west']}"
    elif poly is not None:
        poly_str = ""
        for y,x in poly.exterior.coords:
            poly_str += f"{y},{x} "
        poly_str = poly_str.rstrip(' ')
        return poly_str

def make_xml_filter(bbox: dict, poly: Polygon) -> str:
    """
    Makes an XML filter with optional polygon or bbox constraints
    Used in OGC WFS v1.0.0 "FILTER" parameter
    """
    if bbox is not None or poly is not None:
        # Filter NVCL boreholes and within bbox or polygon
        polygon = make_poly_coords(bbox, poly)
        poly_prop = make_polygon_prop(polygon)
        nvcl_prop = make_nvcl_like_prop()
        return f"""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"><ogc:And>{poly_prop}{nvcl_prop}</ogc:And></ogc:Filter>"""
    # Filter NVCL boreholes only
    return make_nvcl_like_filter()

