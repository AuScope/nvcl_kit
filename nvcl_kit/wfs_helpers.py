import logging
import sys
from types import SimpleNamespace

from shapely import Point, LinearRing, Polygon
from requests.exceptions import RequestException
from http.client import HTTPException
import xml.etree.ElementTree as ET

from nvcl_kit.xml_helpers import clean_xml_parse
from nvcl_kit.cql_filter import make_cql_filter, make_cql_request
from nvcl_kit.xml_filter import make_xml_filter, make_xml_request

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

def get_borehole_list(param_obj: SimpleNamespace) -> tuple[list, bool, bool]:
    prov = param_obj.PROV
    if param_obj.USE_CQL:
        cql_filter = make_cql_filter(param_obj.BBOX, param_obj.POLYGON)
        features = make_cql_request(param_obj.WFS_URL, prov, cql_filter, param_obj.MAX_BOREHOLES)
    else:
        xml_filter = make_xml_filter(param_obj.BBOX, param_obj.POLYGON)
        features = make_xml_request(param_obj.WFS_URL, prov, xml_filter, param_obj.MAX_BOREHOLES)

    if len(features) == 0:
        return [], False, None 

    borehole_list = []
    for feature in features:
        try:
            f = SimpleNamespace()
            props = feature['properties']


            # Get NVCL_ID
            f.nvcl_id = feature['id'].split('.')[-1:][0]

            # Get 3D coords - they are produced as floats
            f.x = float(feature['geometry']['coordinates'][0])
            f.y = float(feature['geometry']['coordinates'][1])
            try:
                f.z = float(props['elevation_m'])
            except (ValueError, KeyError):
                f.z = 0.0

            # Get HREF
            f.href = props['identifier']

            # Loop over possible values (from GeoSciML BoreholeView v4.1) and 'tenement' + 'project'
            for to_attr in ('identifier', 'name', 'description', 'purpose', 'status', 'drillingMethod', 'operator', 'driller', 'drillStartDate', 'drillEndDate', 'startPoint', 'inclinationType', 'boreholeMaterialCustodian', 'boreholeLength_m', 'elevation_m', 'elevation_srs', 'positionalAccuracy', 'source', 'parentBorehole_uri', 'metadata_uri', 'genericSymbolizer', 'tenement', 'project'):
                if to_attr in props:
                    setattr(f, to_attr, str(props[to_attr]))
                else:
                    setattr(f, to_attr, '')

        except Exception as exc:
            LOGGER.debug(f"Exception parsing JSON response from {prov}: {exc}")
            continue
        borehole_list.append(f)
    return borehole_list, True, True
