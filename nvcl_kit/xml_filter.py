import sys
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib3.exceptions import HTTPError
from urllib3.util import Retry

from shapely import LinearRing, MultiPolygon, Polygon
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


def make_xml_request(url: str, prov: str, xml_filter: str, max_features: int) -> list:
    """
    Makes an OGC WFS GetFeature v1.1.0 request using POST and expecting a JSON response
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
        data = f"""<?xml version="1.0" encoding="UTF-8"?>
            <wfs:GetFeature
            service="WFS"
            version="1.1.0"
            xmlns:gsmlp="http://xmlns.geosciml.org/geosciml-portrayal/4.0"
            xmlns:gml="http://www.opengis.net/gml"
            xmlns:wfs="http://www.opengis.net/wfs"
            xmlns:ogc="http://www.opengis.net/ogc"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"
            maxFeatures="1000000"
            startIndex="{str(batch_count)}"
            resultType="results"
            outputFormat="json"
            >
                <wfs:Query typeName="gsmlp:BoreholeView">
                    {xml_filter}
                </wfs:Query>
            </wfs:GetFeature>
            """
        
        data = " ".join([line.strip() for line in data.splitlines()]).encode('utf-8')
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


def encode_polygon_member(poly: Polygon, srid: int) -> str:
    # Ensure exterior ring is CCW as per OGC standards
    if poly.exterior.is_ccw:
        e_coords = " ".join([f"{y} {x}" for y,x in poly.exterior.coords])
    else:
        e_coords = " ".join([f"{y} {x}" for y,x in poly.exterior.coords[::-1]])

    exterior_ring = f"""
        <exterior>
            <LinearRing>
                <posList>{e_coords}</posList>
            </LinearRing>
        </exterior>
    """
    interior_rings = []
    for i in poly.interiors:
        # Ensure interior rings are CW as per OGC standards
        if LinearRing(i).is_ccw:
            i_coords = " ".join([f"{y} {x}" for y, x in i.coords[::-1]])
        else:
            i_coords = " ".join([f"{y} {x}" for y, x in i.coords])

        interior_rings.append(f"""
            <gml:interior>
                <gml:LinearRing>
                    <gml:posList>{i_coords}</gml:posList>
                </gml:LinearRing>
            </gml:interior>
        """)
    
    pgm_str = f"""
            <Polygon xmlns="http://www.opengis.net/gml" srsName="EPSG:{srid}">
                {exterior_ring}
                {''.join(interior_rings)}
            </Polygon>
    """
    pgm_str = "".join([line.strip() for line in pgm_str.splitlines()])
    
    return pgm_str


def make_xml_filter(bbox: dict, poly: Polygon|MultiPolygon|LinearRing, poly_srid: int = 4326, remove_rings: bool = False) -> str:
    """
    Makes an XML filter with optional polygon or bbox constraints
    Used in OGC WFS v1.1.0 "FILTER" parameter
    """

    # If no bbox or polygon provided, return a filter which just checks for 'nvclCollection' = true
    if bbox is None and poly is None:
        return """<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc"><ogc:PropertyIsEqualTo><ogc:PropertyName>gsmlp:nvclCollection</ogc:PropertyName><ogc:Literal>true</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>"""

    if bbox is not None:
        north, south, east, west = bbox['north'], bbox['south'], bbox['east'], bbox['west']
        spatial_filter = f"""
            <ogc:BBOX>
                <ogc:PropertyName>gsmlp:shape</ogc:PropertyName>
                <gml:Envelope srsName="EPSG:{poly_srid}">
                    <gml:lowerCorner>{west} {south}</gml:lowerCorner>
                    <gml:upperCorner>{east} {north}</gml:upperCorner>
                </gml:Envelope>
            </ogc:BBOX>
          """
    elif poly is not None:
        if remove_rings and isinstance(poly, Polygon):
            poly = Polygon(poly.exterior)
        elif remove_rings and isinstance(poly, MultiPolygon):
            poly = MultiPolygon([Polygon(p.exterior) for p in poly.geoms])
        
        if isinstance(poly, LinearRing):
            poly = Polygon(poly)

        polygon_members = []
        if isinstance(poly, MultiPolygon):
            # iterate over each polygon and create a polygonMember for each
            for p in poly.geoms:
                polygon_members.append(encode_polygon_member(p, poly_srid))
        else:
            polygon_members.append(encode_polygon_member(poly, poly_srid))

    # assemble and then strip whitespace and newlines for better readability in logs
        spatial_filter = f"""
            <Intersects
            >
                <ogc:PropertyName>gsmlp:shape</ogc:PropertyName>
                {''.join(polygon_members)}
            </Intersects>
        """
    spatial_filter = " ".join([line.strip() for line in spatial_filter.splitlines()])
    
    return f"""<ogc:Filter><ogc:And>{spatial_filter}<ogc:PropertyIsEqualTo><ogc:PropertyName>gsmlp:nvclCollection</ogc:PropertyName><ogc:Literal>true</ogc:Literal></ogc:PropertyIsEqualTo></ogc:And></ogc:Filter>"""
    

