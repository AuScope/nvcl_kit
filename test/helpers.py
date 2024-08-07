import unittest
from unittest.mock import Mock

from types import SimpleNamespace

import shapely

from nvcl_kit.reader import NVCLReader




def setup_reader() -> NVCLReader:
    ''' Initialises NVCLReader() object

    :returns: NVCLReader() object
    '''
    rdr = None
    with unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True) as mock_wfs:
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('full_wfs_yx.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
            param_obj = setup_param_obj()
            rdr = NVCLReader(param_obj)
    return rdr


def setup_urlopen(fn, params: dict, src_file: str, binary: bool = False, rdr: NVCLReader = None) -> list:
    ''' Patches over 'urlopen()' call and calls a function with parameters

    :param fn: function to call
    :param params: function's parameters as a dict
    :param src_file: filename of a file containing data returned from patched 'urlopen()'
    :param rdr: optional NVCLReader() object
    :returns: data returned from function call
    '''
    # If NVCLReader() is not supplied create one
    if rdr is None:
        rdr = setup_reader()
    ret_list = []
    with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
        open_obj = mock_request.return_value
        if not binary:
            with open(src_file) as fp:
                open_obj.__enter__.return_value.read.return_value = bytes(fp.read(), 'ascii')
        else:
            with open(src_file, 'rb') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
        ret_list = getattr(rdr, fn)(**params)
    return ret_list


def setup_param_obj(max_boreholes: int = None, bbox: dict = None, polygon: shapely.geometry.LinearRing = None, 
        depths: tuple = None, borehole_crs: str = None, cache_path = None) -> SimpleNamespace:
    ''' Create a parameter object for passing to NVCLReader constructor, used for testing only

    :param max_boreholes: maximum number of boreholes to download
    :param bbox: bounding box used to limit boreholes {"west": -180.0,"south": -90.0, ... }
    :param polygon: polygon used to limit boreholes
    :param depths: only retrieve data within this depth range  (0.0, 1230.0)
    :param borehole_crs: borehole coordinate system e.g. 'EPSG:4326'
    :param cache_path: path used to cache network responses to local filesystem
    :returns: SimpleNamespace() object containing parameters
    '''
    param_obj = SimpleNamespace()
    param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
    param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
    if bbox:
        param_obj.BBOX = bbox
    if depths:
        param_obj.DEPTHS = depths
    if polygon:
        param_obj.POLYGON = polygon
    if max_boreholes:
        param_obj.MAX_BOREHOLES = max_boreholes
    if borehole_crs:
        param_obj.BOREHOLE_CRS = borehole_crs
    if cache_path:
        param_obj.CACHE_PATH = cache_path
    return param_obj
