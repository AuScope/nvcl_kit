import sys
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib3.exceptions import HTTPError
from urllib3.util import Retry

from shapely import Polygon
import requests
from requests.adapters import HTTPAdapter

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

def make_xml_request(url: str, prov: str, xml_filter: str, max_features: int) -> list:
    """
    Makes an OGC WFS GetFeature v1.0.0 request using POST and expecting a JSON response
    This also implements local feature filtering for 'nvclCollection' attribute

    :param url: OGC WFS URL
    :param prov: provider e.g. 'nsw'
    :param xml_filter: XML filter string e.g. filter by polygon
    :param max_features: maximum number of features to return, if < 1 then all boreholes are returned
    :returns: list of features, each feature is a dict
    """
    batch_count = 0
    done = False
    feat_list = []
    feat_ids = set()
    LOOP_MAX = 10000000

    # This is designed for the NTGS WFS borehole service which does not respond to CQL filter requests

    # Loop which pages through all the WFS requests
    while not done:
        # Check the filter is a non-empty string, otherwise use a default filter which just checks for 'nvclCollection' = true
        if not isinstance(xml_filter, str):
            xml_filter = ""
        data = f"""
            <GetFeature
            xmlns:ogc="http://www.opengis.net/ogc"
            service="WFS"
            version="1.1.0"
            maxFeatures="10000"
            startIndex="{str(batch_count)}"
            resultType="results"
            outputFormat="json"
            >
                <Query typeName="gsmlp:BoreholeView">
                    {xml_filter}
                    <ogc:SortBy>
                        <ogc:SortProperty>
                            <ogc:PropertyName>nvclCollection</ogc:PropertyName>
                            <ogc:SortOrder>DESC</ogc:SortOrder>
                        </ogc:SortProperty>
                    </ogc:SortBy>
                </Query>
            </GetFeature>
            """
        # Send the POST request with the XML payload 
        try:
            with requests.Session() as s:

                # Retry with backoff
                retries = Retry(total=NUM_RETRIES,
                                backoff_factor=BACKOFF_FACTOR,
                                status_forcelist=HTTP_RETRY_CODES,
                                allowed_methods=["POST"]
                            )
                s.mount('https://', HTTPAdapter(max_retries=retries))

                # Sending the request
                response = s.post(url, data=data)
        except (HTTPError, requests.RequestException) as e:
            LOGGER.error(f"{prov} returned error sending WFS GetFeature: {e}")
            return feat_list

        # Check if the request was successful
        if response.status_code == 200:
            try:
                resp = response.json()
            except (TypeError, requests.JSONDecodeError) as e:
                LOGGER.error(f"Error parsing JSON from {prov} WFS GetFeature response: {e}")
                return feat_list
            
            # If no more features left we can exit
            if len(resp['features']) == 0:
                return feat_list

            # Collect the NVCL features
            for f in resp['features']:
                if f['properties']['nvclCollection'] == 'true':
                    feat_list.append(f)
                    feat_ids.add(f['id'])

                # Exit when we reach maximum features limit
                if max_features > 0 and len(feat_list) == max_features:
                    return feat_list

            batch_count += len(resp['features'])

            # Emergency exit
            if batch_count > LOOP_MAX:
                return feat_list

        else:
            LOGGER.error(f"{prov} returned error {response.status_code} in WFS GetFeature response: {response.text}")
            break
    return feat_list


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
    Used in OGC WFS v1.1.0 "FILTER" parameter
    """
    if bbox is not None or poly is not None:
        # Filter within bbox or polygon
        polygon = make_poly_coords(bbox, poly)
        poly_prop = make_polygon_prop(polygon)
        return f"""<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"><ogc:And>{poly_prop}<PropertyIsEqualTo><PropertyName>gsmlp:nvclCollection</PropertyName><Literal>true</Literal></PropertyIsEqualTo></ogc:And></ogc:Filter>"""
    return "<ogc:Filter><PropertyIsEqualTo><PropertyName>gsmlp:nvclCollection</PropertyName><Literal>true</Literal></PropertyIsEqualTo></ogc:Filter>"

