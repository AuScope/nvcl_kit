"""
This module contains functions used to build a set of NVCL service connection parameters
"""

import sys
import logging
from types import SimpleNamespace


LOG_LVL = logging.INFO
''' Initialise debug level, set to 'logging.INFO' or 'logging.DEBUG' '''

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


def param_builder(provider: str, **options: dict) -> SimpleNamespace:
    """
    Builds a set of parameters which can be passed to 'NVCLReader' for connecting to an NVCL service

    :param provider: state or territory name, one of: 'nsw', 'tas', 'vic', 'qld', 'nt', 'sa', 'wa', 'csiro'
    :param options: optional keyword parameters
                   bbox: 2D bounding box in EPSG:4326, only boreholes within box are retrieved, default {"west": -180.0,"south": -90.0,"east": 180.0,"north": 0.0})
                   polygon: 2D 'shapely.Polygon' y/x axis order, EPSG:4326, limit to boreholes within this polygon
                   depths: Tuple of range of depths (min,max) [metres]
                   wfs_url: URL of WFS service, GeoSciML V4.1 BoreholeView
                   nvcl_url: URL of NVCL service
                   max_boreholes: Maximum number of boreholes to retrieve. If < 1 then all boreholes are loaded, default 0
                   use_cql: use "CQL_FILTER" in WFS GetFeature requests. Geoserver only.
                   cache_path: the folder path for cache files

    :returns: a SimpleNamespace object containing required connection parameters
    """
    OPTION_LIST = ['bbox', 'polygon', 'depths', 'wfs_url', 'nvcl_url',
                   'max_boreholes', 'use_cql', 'cache_path']
    # Deprecated options
    OLD_OPTION_LIST = ['borehole_crs', 'wfs_version', 'use_local_filtering']

    # Check if options are valid
    for opt in options:
        if opt in OLD_OPTION_LIST:
            LOGGER.warning(f"{opt} is a deprecated param_builder option")
        elif opt not in OPTION_LIST :
            LOGGER.warning(f"{opt} is not a valid param_builder option")
            return None

    # Remove deprecated options
    for old_opt in OLD_OPTION_LIST:
        options.pop(old_opt, None)
        
    # Check provider string
    if not isinstance(provider, str):
        LOGGER.warning("Provider parameter must be a string e.g. 'nsw', 'qld', 'vic'")
        return None
    param_obj = SimpleNamespace()

    # Tasmania
    if provider.lower() in ['tas', 'tasmania']:
        param_obj.PROV = 'tas'
        param_obj.WFS_URL = "https://www.mrt.tas.gov.au/web-services/ows"
        param_obj.NVCL_URL = "https://www.mrt.tas.gov.au/NVCLDataServices/"
        param_obj.USE_CQL = True

    # Victoria
    elif provider.lower() in ['vic', 'victoria']:
        param_obj.PROV = 'vic'
        param_obj.WFS_URL = "https://geology.data.vic.gov.au/nvcl/ows"
        param_obj.NVCL_URL = "https://geology.data.vic.gov.au/NVCLDataServices/"
        param_obj.USE_CQL = True

    # New South Wales
    elif provider.lower() in ['nsw', 'new south wales']:
        param_obj.PROV = 'nsw'
        param_obj.WFS_URL = "https://gs.geoscience.nsw.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://nvcl.geoscience.nsw.gov.au/NVCLDataServices/"
        param_obj.USE_CQL = True

    # Queensland
    elif provider.lower() in ['qld', 'queensland']:
        param_obj.PROV = 'qld'
        param_obj.WFS_URL = "https://geology.information.qld.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://geology.information.qld.gov.au/NVCLDataServices/"
        param_obj.USE_CQL = True

    # Northern Territory
    elif provider.lower() in ['nt', 'northern territory']:
        param_obj.PROV = 'nt'
        param_obj.WFS_URL = "https://geology.data.nt.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://geology.data.nt.gov.au/NVCLDataServices/"
        param_obj.USE_CQL = False # NT's geoserver is misconfigured and CQL does not work

    # South Australia
    elif provider.lower() in ['sa', 'south australia']:
        param_obj.PROV = 'sa'
        param_obj.WFS_URL = "https://sarigdata.pir.sa.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://sarigdata.pir.sa.gov.au/nvcl/NVCLDataServices/"
        param_obj.USE_CQL = True

    # Western Australia
    elif provider.lower() in ['wa', 'western australia']:
        param_obj.PROV = 'wa'
        param_obj.WFS_URL = "https://geossdi.dmp.wa.gov.au/services/ows"
        param_obj.NVCL_URL = "https://geossdi.dmp.wa.gov.au/NVCLDataServices/"
        param_obj.USE_CQL = True

    # CSIRO
    elif provider.lower() == 'csiro':
        param_obj.PROV = 'csiro'
        param_obj.WFS_URL = "https://nvclwebservices.csiro.au/geoserver/ows"
        param_obj.NVCL_URL = "https://nvclwebservices.csiro.au/NVCLDataServices/"
        param_obj.USE_CQL = True

    else:
        LOGGER.warning("Cannot recognise provider parameter e.g. 'vic' 'sa' etc.")
        return None

    # Set up optional parameters 
    # Either 'bbox' or 'polygon', but not both
    if 'bbox' in options:
        param_obj.BBOX = options['bbox']
    elif 'polygon' in options:
        param_obj.POLYGON = options['polygon']

    # Set all remaining parameters
    for p in OPTION_LIST[2:]:
        if p in options:
            setattr(param_obj, p.upper(), options[p])

    return param_obj
