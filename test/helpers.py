import unittest
from unittest.mock import Mock

from types import SimpleNamespace


from nvcl_kit.reader import NVCLReader



def setup_reader():
    ''' Initialises NVCLReader() object

    :returns: NVCLReader() object
    '''
    rdr = None
    with unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True) as mock_wfs:
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('full_wfs3.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
            param_obj = setup_param_obj()
            rdr = NVCLReader(param_obj)
    return rdr


def setup_urlopen(fn, params, src_file, binary=False):
    ''' Patches over 'urlopen()' call and calls a function with parameters

    :param fn: function to call
    :param params: function's parameters as a dict
    :param src_file: filename of a file containing data returned from patched 'urlopen()'
    :returns: data returned from function call
    '''
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


def setup_param_obj(max_boreholes=None, bbox=None, polygon=None, depths=None):
    ''' Create a parameter object for passing to NVCLReader constructor

    :param max_boreholes: maximum number of boreholes to download
    :param bbox: bounding box used to limit boreholes
    :param polygon: polygon used to limit boreholes
    :param depths: only retrieve data within this depth range
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
    return param_obj