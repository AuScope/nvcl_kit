import unittest
from unittest.mock import Mock, MagicMock
from io import IOBase
import json

from types import SimpleNamespace

import shapely

from nvcl_kit.reader import NVCLReader


def setup_reqs_obj(inp, reqs_obj):
    ''' Set up the mock requests get() reponse

    :param inp: string or file object containing the desired response
    :param reqs_obj: return value of the Mock get() request object
    :return: new Mock get() request object, JSON response
    '''
    if isinstance(inp, IOBase):
        resp_str = inp.read().rstrip('\n')
    else:
        resp_str = inp
    try:
        json_obj = json.loads(resp_str)
    except (TypeError, json.JSONDecodeError, UnicodeDecodeError) as e:
        json_obj = None
    reqs_obj.text = resp_str
    reqs_obj.status_code = 200
    if json_obj is not None:
        reqs_obj.json = MagicMock()
        reqs_obj.json.return_value = {"features": json_obj["features"]}
    return reqs_obj, json_obj


def setup_reader() -> NVCLReader:
    ''' Initialises NVCLReader() object

    :returns: NVCLReader() object
    '''
    rdr = None
    with unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get', autospec=True) as mock_reqs:
        reqs_obj = mock_reqs.return_value
        with open('full_wfs_cql.json') as fp:
            reqs_obj = setup_reqs_obj(fp, reqs_obj)
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
        depths: tuple = None, borehole_crs: str = None, cache_path = None, use_cql = None) -> SimpleNamespace:
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
    if use_cql:
        param_obj.USE_CQL = use_cql
    param_obj.PROV = 'blah'
    return param_obj
