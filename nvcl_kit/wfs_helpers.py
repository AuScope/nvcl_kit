import logging
import sys

from owslib.fes import PropertyIsLike, etree
from shapely.geometry.polygon import Point
from requests.exceptions import RequestException
from owslib.util import ServiceException
from http.client import HTTPException
import xml.etree.ElementTree as ET

from nvcl_kit.xml_helpers import clean_xml_parse

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

# Namespaces for WFS Borehole response
NS = {'wfs': "http://www.opengis.net/wfs",
      'xs': "http://www.w3.org/2001/XMLSchema",
      'it.geosolutions': "http://www.geo-solutions.it",
      'mo': "http://xmlns.geoscience.gov.au/minoccml/1.0",
      'topp': "http://www.openplans.org/topp",
      'mt': "http://xmlns.geoscience.gov.au/mineraltenementml/1.0",
      'nvcl': "http://www.auscope.org/nvcl",
      'gsml': "urn:cgi:xmlns:CGI:GeoSciML:2.0",
      'ogc': "http://www.opengis.net/ogc",
      'gsmlp': "http://xmlns.geosciml.org/geosciml-portrayal/4.0",
      'sa': "http://www.opengis.net/sampling/1.0",
      'ows': "http://www.opengis.net/ows",
      'om': "http://www.opengis.net/om/1.0",
      'xlink': "http://www.w3.org/1999/xlink",
      'gml': "http://www.opengis.net/gml",
      'er': "urn:cgi:xmlns:GGIC:EarthResource:1.1",
      'xsi': "http://www.w3.org/2001/XMLSchema-instance",
      'gml32': "http://www.opengis.net/gml/3.2"}

# From GeoSciML BoreholeView 4.1
GSMLP_IDS = ['identifier', 'name', 'description', 'purpose', 'status', 'drillingMethod',
             'operator', 'driller', 'drillStartDate', 'drillEndDate', 'startPoint',
             'inclinationType', 'boreholeMaterialCustodian', 'boreholeLength_m',
             'elevation_m', 'elevation_srs', 'positionalAccuracy', 'source', 'parentBorehole_uri',
             'metadata_uri', 'genericSymbolizer']


def get_feature(wfs, param_obj):
    response_str = b''
    bhv_list = []
    # Don't use local filtering, can be both WFS v1.1.0 or v2.0.0
    if not param_obj.USE_LOCAL_FILTERING:
        # FIXME: Can't filter for BBOX and nvclCollection==true at the same time
        # [owslib's BBox uses 'ows:BoundingBox', not supported in WFS]
        # so is best to do the BBOX manually
        filter_prop = PropertyIsLike(propertyname='gsmlp:nvclCollection', literal='true', matchCase=False)
        # filter_2 = BBox([param_obj.BBOX['west'], param_obj.BBOX['south'], param_obj.BBOX['east'],
        #              param_obj.BBOX['north']], crs=param_obj.BOREHOLE_CRS)
        # filter_3 = And([filter_, filter_2])
        filterxml = etree.tostring(filter_prop.toXML()).decode("utf-8")
        try:
            getfeat_params = {'typename': 'gsmlp:BoreholeView', 'filter': filterxml}
            if param_obj.WFS_VERSION != '2.0.0':
                getfeat_params['srsname'] = param_obj.BOREHOLE_CRS
            response_str = clean_resp(wfs, getfeat_params)
        except (RequestException, HTTPException, ServiceException, OSError) as exc:
            LOGGER.warning(f"WFS GetFeature failed, filter={filterxml}: {exc}")
            return bhv_list
        root = clean_xml_parse(response_str)
        return root.findall('./*/gsmlp:BoreholeView', NS)

    # Using local filtering, only supported in WFS v2.0.0
    elif param_obj.WFS_VERSION == "2.0.0":
        RECORD_INC = 10000
        record_cnt = 0
        done = False
        bhv_list = []
        while not done:
            try:
                getfeat_params = {'typename': 'gsmlp:BoreholeView',
                                  'maxfeatures': RECORD_INC,
                                  'startindex': record_cnt}
                # SRS name is not a parameter in v2.0.0
                LOGGER.debug(f'get_feature(): getfeat_params = {getfeat_params}')
                resp_s = clean_resp(wfs, getfeat_params)
                LOGGER.debug(f'get_feature(): resp_s = {resp_s}')
            except (RequestException, HTTPException, ServiceException, OSError) as exc:
                LOGGER.warning(f"WFS GetFeature failed: {exc}")
                return bhv_list
            record_cnt += RECORD_INC
            root = clean_xml_parse(resp_s)
            bhv_list += [x for x in root.findall('./*/gsmlp:BoreholeView', NS)]
            num_ret = root.attrib.get('numberReturned', '0')
            LOGGER.debug(f'get_feature(): num_ret = {num_ret}')
            LOGGER.debug(f'record_cnt = {record_cnt}')
            done = num_ret == '0'

        return bhv_list
    else:
        LOGGER.error("Cannot have USE_LOCAL_FILTERING and WFS_VERSION < 2.0.0")
        return []

def clean_resp(wfs, getfeat_params):
    '''
    Fetches WFS response from owslib and make sure it returns a byte string

    :param wfs: WFS object from OWSLib
    :param getfeat_params: dict of parameters for WFS GetFeature request

    :returns: byte string response
    '''
    
    LOGGER.debug(f"clean_resp(params={getfeat_params})")
    response = wfs.getfeature(**getfeat_params).read()
    LOGGER.debug(f"clean_resp(): response={response}")
    if not type(response) in [bytes, str]:
        response_str = b""
    elif type(response) == bytes:
        response_str = response
    else:
        response_str = response.encode('utf-8', 'ignore')
    return response_str

def fetch_wfs_bh_list(wfs, param_obj, names=[], ids=[]):
    ''' Returns a list of WFS borehole data within bounding box, but only NVCL boreholes
        [ { 'nvcl_id': XXX, 'x': XXX, 'y': XXX, 'href': XXX, ... }, { ... } ]
        See description of 'get_boreholes_list()' for more info

    :returns: borehole list if operation succeeded, else []
    '''
    LOGGER.debug("fetch_wfs_bh_list()")
    bhv_list = get_feature(wfs, param_obj)
    if len(bhv_list) == 0:
        LOGGER.debug('fetch_wfs_bh_list(): No response')
        return [] 
    LOGGER.debug(f'len(bhv_list) = {len(bhv_list)}')
    LOGGER.debug(f'bhv_list = {repr(bhv_list)}')
    borehole_cnt = 0
    record_cnt = 0
    borehole_list = []

    for i in range(len(bhv_list)):
        LOGGER.debug(f'i = {i}')
        child = bhv_list[i]
        LOGGER.debug(f'len(bhv_list) = {len(bhv_list)}')
        LOGGER.debug(f'child = {ET.tostring(child)}')
        # WFS v2.0.0 uses gml32
        if param_obj.WFS_VERSION == '2.0.0':
            id_str = '{' + NS['gml32'] + '}id'
        else:
            id_str = '{' + NS['gml'] + '}id'
        nvcl_id = child.attrib.get(id_str, '').split('.')[-1:][0]

        # Some services don't use a namepace for their id
        if nvcl_id == '':
            nvcl_id = child.attrib.get('id', '').split('.')[-1:][0]

        is_nvcl = child.findtext('./gsmlp:nvclCollection', default="?????", namespaces=NS)
        LOGGER.debug(f"is_nvcl = {is_nvcl}")
        LOGGER.debug(f"nvcl_id = {nvcl_id}")
        if is_nvcl.lower() == "true":
            borehole_dict = {'nvcl_id': nvcl_id}

            # Finds borehole collar x,y assumes units are degrees
            x_y = child.findtext('./gsmlp:shape/gml:Point/gml:pos', default="? ?",
                                 namespaces=NS).split(' ')
            reverse_coords = False
            if x_y == ['?', '?']:
                point = child.findtext('./gsmlp:shape', default="POINT(0.0 0.0)", namespaces=NS).strip(' ')
                reverse_coords = True
                x_y = point.partition('(')[2].rstrip(')').split(' ')
            LOGGER.debug(f'x_y = {x_y}')

            try:
                # See https://docs.geoserver.org/latest/en/user/services/wfs/axis_order.html#wfs-basics-axis
                if param_obj.BOREHOLE_CRS != 'EPSG:4326' or \
                       reverse_coords:
                    # latitude/longitude or y,x order
                    borehole_dict['y'] = float(x_y[0])  # lat
                    borehole_dict['x'] = float(x_y[1])  # lon
                else:
                    # longitude/latitude or x,y order
                    borehole_dict['x'] = float(x_y[0])  # lon
                    borehole_dict['y'] = float(x_y[1])  # lat
            except (OSError, ValueError) as os_exc:
                LOGGER.warning(f"Cannot parse collar coordinates {os_exc}")
                continue

            borehole_dict['href'] = child.findtext('./gsmlp:identifier',
                                                   default="", namespaces=NS)

            # Finds most of the borehole details
            for tag in GSMLP_IDS:
                if tag != 'identifier':
                    borehole_dict[tag] = child.findtext('./gsmlp:'+tag, default="",
                                                        namespaces=NS)

            elevation = child.findtext('./gsmlp:elevation_m', default="0.0", namespaces=NS)
            try:
                borehole_dict['z'] = float(elevation)
            except ValueError:
                borehole_dict['z'] = 0.0

            LOGGER.debug(f"borehole_dict = {repr(borehole_dict)}\n"
                         f"BBOX={param_obj.BBOX}\n"
                         f"{param_obj.BBOX['west']} < {borehole_dict['x']},"
                         f"{param_obj.BBOX['east']} > {borehole_dict['x']}\n"
                         f"{param_obj.BBOX['north']} > {borehole_dict['y']},"
                         f"{param_obj.BBOX['south']} < {borehole_dict['y']}")

            # If POLYGON is set, only accept if within linear ring
            if hasattr(param_obj, 'POLYGON'):
                point = Point(borehole_dict['x'], borehole_dict['y'])
                if point.within(param_obj.POLYGON):
                    borehole_cnt += 1
                    borehole_list.append(borehole_dict)
                    LOGGER.debug(f"borehole_cnt = {borehole_cnt}")

            # Else only accept if within bounding box
            elif (param_obj.BBOX['west'] < borehole_dict['x'] and
                  param_obj.BBOX['east'] > borehole_dict['x'] and
                  param_obj.BBOX['north'] > borehole_dict['y'] and
                  param_obj.BBOX['south'] < borehole_dict['y']):
                borehole_cnt += 1
                borehole_list.append(borehole_dict)
                LOGGER.debug(f"borehole_cnt = {borehole_cnt}")

            if param_obj.MAX_BOREHOLES > 0 and borehole_cnt >= param_obj.MAX_BOREHOLES:
                break
        record_cnt += 1
        LOGGER.debug(f'record_cnt = {record_cnt}')
    LOGGER.debug(f'fetch_boreholes_list() returns {len(borehole_list)}')
    return borehole_list

