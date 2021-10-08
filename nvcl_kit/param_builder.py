from types import SimpleNamespace

def param_builder(state, **options):
    param_obj = SimpleNamespace()
    if not type(state) != 'str':
        return False, "state parameter must be a string e.g. 'nsw', 'qld', 'vic'"

    # Tasmania
    if state.lower() in ['tas', 'tasmania']:
        param_obj.WFS_URL = "https://www.mrt.tas.gov.au/web-services/ows"
        param_obj.NVCL_URL = "https://www.mrt.tas.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Victoria
    elif state.lower() in ['vic', 'victoria']:
        param_obj.WFS_URL = "https://geology.data.vic.gov.au/nvcl/ows"
        param_obj.NVCL_URL = "https://geology.data.vic.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # New South Wales
    elif state.lower() in ['nsw', 'new south wales']:
        param_obj.WFS_URL = "https://gs.geoscience.nsw.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://nvcl.geoscience.nsw.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Queensland
    elif state.lower() in ['qld', 'queensland']:
        param_obj.WFS_URL = "https://geology.information.qld.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://geology.information.qld.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Northern Territory
    elif state.lower() in ['nt', 'northern territory']:
        param_obj.WFS_URL = "http://geology.data.nt.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "http://geology.data.nt.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = True
        param_obj.WFS_VERSION = "2.0.0"

    # South Australia
    elif state.lower() in ['sa', 'south australia']:
        param_obj.WFS_URL = "https://sarigdata.pir.sa.gov.au/geoserver/ows"
        param_obj.NVCL_URL = "https://sarigdata.pir.sa.gov.au/nvcl/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "1.1.0"

    # Western Australia
    elif state.lower() in ['wa', 'western australia']:
        param_obj.WFS_URL = "https://geossdi.dmp.wa.gov.au/services/ows"
        param_obj.NVCL_URL = "https://geossdi.dmp.wa.gov.au/NVCLDataServices/"
        param_obj.USE_LOCAL_FILTERING = False
        param_obj.WFS_VERSION = "2.0.0"

    else:
        return False, "Cannot recognise state parameter e.g. 'vic' 'sa' etc."    

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
