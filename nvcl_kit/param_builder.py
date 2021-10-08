from types import SimpleNamespace

def param_builder(provider, **options):
    """
    :param provider: state or territory name, one of: 'nsw', 'tas', 'vic', 'qld', 'nt', 'sa', 'wa'
    :param options: optional keyword parameters
                   bbox: 2D bounding box in EPSG:4326, only boreholes within box are retrieved
                         default {"west": -180.0,"south": -90.0,"east": 180.0,"north": 0.0})
                   polygon: 2D 'shapely.geometry.LinearRing' object, only boreholes within this ring are retrieved
                   borehole_crs: CRS string, default "EPSG:4326"
                   wfs_version: WFS version string, default "1.1.0"
                   depths: Tuple of range of depths (min,max) [metres]
                   wfs_url: URL of WFS service, GeoSciML V4.1 BoreholeView
                   nvcl_url: URL of NVCL service
                   max_boreholes: Maximum number of boreholes to retrieve. If < 1 then all boreholes are loaded
                                  default 0
    """
    param_obj = SimpleNamespace()
    if not type(provider) != 'str':
        return False, "provider parameter must be a string e.g. 'nsw', 'qld', 'vic'"

    # Tasmania
    if provider.lower() in ['tas', 'tasmania']:
        param_obj.WFS_URL = "https://www.mrt.tas.gov.au/web-services/ows"
        param_obj.NVCL_URL = "https://www.mrt.tas.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Victoria
    elif provider.lower() in ['vic', 'victoria']:
        param_obj.WFS_URL = "https://geology.data.vic.gov.au/nvcl/ows"
        param_obj.NVCL_URL = "https://geology.data.vic.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # New South Wales
    elif provider.lower() in ['nsw', 'new south wales']:
        param_obj.WFS_URL = "https://gs.geoscience.nsw.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://nvcl.geoscience.nsw.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Queensland
    elif provider.lower() in ['qld', 'queensland']:
        param_obj.WFS_URL = "https://geology.information.qld.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://geology.information.qld.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Northern Territory
    elif provider.lower() in ['nt', 'northern territory']:
        param_obj.WFS_URL = "http://geology.data.nt.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "http://geology.data.nt.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = True
        param_obj.WFS_VERSION = "2.0.0"

    # South Australia
    elif provider.lower() in ['sa', 'south australia']:
        param_obj.WFS_URL = "https://sarigdata.pir.sa.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://sarigdata.pir.sa.gov.au/nvcl/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Western Australia
    elif provider.lower() in ['wa', 'western australia']:
        param_obj.WFS_URL = "https://geossdi.dmp.wa.gov.au/services/ows"
        param_obj.NVCL_URL = "https://geossdi.dmp.wa.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "2.0.0"

    else:
        return False, "Cannot recognise provider parameter e.g. 'vic' 'sa' etc."    

    # Optional parameters
    if 'bbox' in options:
        param_obj.BBOX = options['bbox']
    elif 'polygon' in options:
        param_obj.POLYGON = options['polygon']
    if 'borehole_crs' in options:
        param_obj.BOREHOLE_CRS = options['borehole_crs']
    if 'wfs_version' in options:
        param_obj.WFS_VERSION = options['wfs_version']
    if 'depths' in options:
        param_obj.DEPTHS = options['depth']
    if 'wfs_url' in options:
        param_obj.WFS_URL = options['wfs_url']
    if 'nvcl_url' in options:
        param_obj.NVCL_URL = options['nvcl_url']
    if 'max_boreholes' in options:
        param_obj.MAX_BOREHOLES = options['max_boreholes']
    if 'use_local_filtering' in options:
        param_obj.USE_LOCAL_FILTERING = options['use_local_filtering']

    return True, param_obj
