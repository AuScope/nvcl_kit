#!/usr/bin/env python3
import sys, os
import unittest
from unittest.mock import patch, Mock
from requests.exceptions import Timeout, RequestException
from owslib.util import ServiceException
from http.client import HTTPException
import logging

from types import SimpleNamespace

from nvcl_kit.reader import NVCLReader

MAX_BOREHOLES = 20

'''
To run this from the command line to test code in local repo:

$ export PYTHONPATH=$HOME/gitlab/nvcl_kit
$ python -m unittest test_reader.py

or use 'tox' to test the packaged 'pypi' version 

'''

class TestNVCLReader(unittest.TestCase):


    def setup_param_obj(self, max_boreholes=None, bbox=None, polygon=None, depths=None):
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


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_logging_level(self, mock_wfs):
        ''' Test the 'log_lvl' parameter in the constructor
        '''
        # Use an empty response
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('empty_wfs.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.readline()
            with self.assertLogs('nvcl_kit.wfs_helpers', level='DEBUG') as nvcl_log:
                param_obj = SimpleNamespace()
                param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
                param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
                rdr = NVCLReader(param_obj, log_lvl=logging.DEBUG)
                self.assertTrue(len(nvcl_log.output)>0, "Missing 'fetch_wfs_bh_list()' in output")
                self.assertIn("fetch_wfs_bh_list()", nvcl_log.output[0])


    def try_input_param(self, param_obj, msg):
        ''' Used to test variations in erroneous constructor input parameters
            :param param_obj: input parameter object
            :param msg: warning messge produced
        '''
        with self.assertLogs('nvcl_kit.reader', level='WARN') as nvcl_log:
            rdr = NVCLReader(param_obj)
            self.assertTrue(len(nvcl_log.output)>0, f"Missing '{msg}' in output")
            self.assertIn(msg, nvcl_log.output[0])
            self.assertEqual(rdr.wfs, None)


    def test_bad_constr_param(self):
        ''' Tests that if it has bad 'param_obj' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        self.try_input_param({'ffgf':43},
                              "'param_obj' is not a SimpleNamespace() object")


    def test_bad_crs_param(self):
        ''' Tests that if has a bad 'BOREHOLE_CRS' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BOREHOLE_CRS = "blah"
        self.try_input_param(param_obj, "'BOREHOLE_CRS' parameter is not an EPSG string")


    def test_bad_wfs_ver_param1(self):
        ''' Tests that if has a bad 'WFS_VERSION' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.WFS_VERSION = 1.1
        self.try_input_param(param_obj, "'WFS_VERSION' parameter is not a numeric string")


    def test_bad_wfs_ver_param2(self):
        ''' Tests that if has a badly formatted 'WFS_VERSION' parameter it
            issues a warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.WFS_VERSION = "v1.1"
        self.try_input_param(param_obj, "'WFS_VERSION' parameter is not a numeric string")


    def test_bad_maxbh_param(self):
        ''' Tests that if has a bad 'MAX_BOREHOLES' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.MAX_BOREHOLES = "blah"
        self.try_input_param(param_obj, "'MAX_BOREHOLES' parameter is not an integer")


    def test_bad_bbox_param1(self):
        ''' Tests that if has a bad 'BBOX' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BBOX = "blah"
        self.try_input_param(param_obj, "'BBOX' parameter is not a dict")


    def test_bad_bbox_param2(self):
        ''' Tests that if it is missing part of 'BBOX' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BBOX = { 'north': 0, 'west':90, 'east':180 }
        self.try_input_param(param_obj, "BBOX['south'] parameter is missing")


    def test_bad_bbox_param3(self):
        ''' Tests that if part of 'BBOX' parameter is not a number it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BBOX = { 'south': '-40', 'north': 0, 'west': 90, 'east':180 }
        self.try_input_param(param_obj, "BBOX['south'] parameter is not a number")

    def test_bad_polygon_param(self):
        ''' Tests if 'POLYGON' parameter is not assigned properly, it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.POLYGON = []
        self.try_input_param(param_obj,"'POLYGON' parameter is not a shapely.geometry.polygon.LinearRing")
 
    def test_missing_wfs_param(self):
        ''' Tests that if it is missing 'WFS_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        self.try_input_param(param_obj, "'WFS_URL' parameter is missing")


    def test_bad_wfs_param(self):
        ''' Tests that if it has a bad 'WFS_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = None
        self.try_input_param(param_obj, "'WFS_URL' parameter is not a string")


    def test_missing_nvcl_param(self):
        ''' Tests that if it is missing 'NVCL_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        self.try_input_param(param_obj, "'NVCL_URL' parameter is missing")


    def test_bad_nvcl_param(self):
        ''' Tests that if it has a bad 'NVCL_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = None
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        self.try_input_param(param_obj, "'NVCL_URL' parameter is not a string")


    def test_bad_depth_param(self):
        ''' Tests that if it has a bad 'DEPTH' parameter it issues a 
            warning message and returns wfs attribute as None
        '''
        for depths, err_str in [(None, "'DEPTHS' parameter is not a tuple"),
                                (("A","B","C"), "'DEPTHS' parameter does not have length of 2"),
                                ((0, "5"), "'DEPTHS' parameter does not contain numerics"),
                                (("0", 5), "'DEPTHS' parameter does not contain numerics"),
                                ((50,49), "'DEPTHS' parameter minimum is not less then maximum")]:
            param_obj = SimpleNamespace()
            param_obj.DEPTHS = depths
            param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
            self.try_input_param(param_obj, err_str)


    def test_bad_use_local_filt_param(self):
        ''' Tests that if the 'USE_LOCAL_FILTERING' is a bad value it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.USE_LOCAL_FILTERING = "True"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        self.try_input_param(param_obj, "'USE_LOCAL_FILTERING' parameter is not boolean")


    def wfs_exception_tester(self, mock_wfs, excep, msg):
        ''' Creates an exception in owslib getfeature() read()
            and tests to see that the correct warning message is generated

        :param mock_wfs: mock version of WebFeatureService() object
        :param excep: exception that is to be created
        :param msg: warning message to test for
        '''
        mock_wfs.side_effect = excep
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        wfs_obj.getfeature.return_value.read.side_effect = excep
        with self.assertLogs('nvcl_kit.reader', level='WARN') as nvcl_log:
            param_obj = self.setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            self.assertTrue(len(nvcl_log.output)>0, f"Missing '{msg}' in output")
            self.assertIn(msg, nvcl_log.output[0])
            self.assertEqual(rdr.wfs, None)


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_exception_wfs(self, mock_wfs):
        ''' Tests that NVCLReader() can handle exceptions in WebFeatureService
            function
        '''
        self.wfs_exception_tester(mock_wfs, ServiceException, 'WFS error:')
        self.wfs_exception_tester(mock_wfs, RequestException, 'Request error:')
        self.wfs_exception_tester(mock_wfs, HTTPException, 'HTTP error code returned:')
        self.wfs_exception_tester(mock_wfs, OSError, 'OS Error:')


    def wfs_read_exception_tester(self, mock_wfs, excep, msg):
        ''' Creates an exception in owslib getfeature() and tests for the
            correct warning message
        :param mock_wfs: mock version of WebFeatureService() object
        :param excep: exception that is to be created
        :param msg: warning message to test for
        '''
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        wfs_obj.getfeature.return_value.read.side_effect = excep
        with self.assertLogs('nvcl_kit.wfs_helpers', level='WARN') as nvcl_log:
            param_obj = self.setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertTrue(len(nvcl_log.output)>0, f"Missing '{msg}' in output")
            self.assertIn(msg, nvcl_log.output[0])
            self.assertEqual(rdr.wfs, None)


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_exception_getfeature_read(self, mock_wfs):
        ''' Tests that can handle exceptions in getfeature's read() function
        '''
        for excep in [Timeout, RequestException, HTTPException, ServiceException, OSError]:
            self.wfs_read_exception_tester(mock_wfs, excep, 'WFS GetFeature failed')


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_none_wfs(self, mock_wfs):
        ''' Test that it does not crash upon 'None', empty string, non-ascii byte string responses
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        bad_byte_str = b'\xff\xff\xff'
        byte_str = b'Test String \xf0\x9f\x98\x80'
        utf_str = byte_str.decode('utf-8')
        for resp in [None, b"", "", byte_str, bad_byte_str, utf_str, []]:
            wfs_obj = mock_wfs.return_value
            wfs_obj.getfeature.return_value = Mock()
            wfs_obj.getfeature.return_value.read.return_value = resp
            param_obj = self.setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(l, [])
            l = rdr.get_nvcl_id_list()
            self.assertEqual(l, [])
            # Check that read() is called once only
            if hasattr(wfs_obj.getfeature.return_value.read, 'assert_called_once'):
                wfs_obj.getfeature.return_value.read.assert_called_once()


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_empty_wfs(self, mock_wfs):
        ''' Test empty but valid WFS response
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('empty_wfs.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.readline()
            param_obj = self.setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(l, [])
            l = rdr.get_nvcl_id_list()
            self.assertEqual(l, [])
            # Check that read() is called once only
            if hasattr(wfs_obj.getfeature.return_value.read, 'assert_called_once'):
                wfs_obj.getfeature.return_value.read.assert_called_once()


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_max_bh_wfs(self, mock_wfs):
        ''' Test full WFS response, maximum number of boreholes is enforced
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('full_wfs3.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
            param_obj = self.setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(len(l), MAX_BOREHOLES)
            l = rdr.get_nvcl_id_list()
            self.assertEqual(len(l), MAX_BOREHOLES)


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_all_bh_wfs(self, mock_wfs):
        ''' Test full WFS response, unlimited number of boreholes
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('full_wfs3.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
            param_obj = self.setup_param_obj()
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(len(l), 102)
            # Test with all fields having values
            self.assertEqual(l[4], {
                'nvcl_id': '12991',
                'x': 145.67616489, 'y': -41.61921239,
                'href': 'http://www.blah.gov.au/resource/feature/blah/borehole/12991',
                'name': 'MC3',
                'description': 'descr',
                'purpose': 'purp',
                'status': 'STATUS',
                'drillingMethod': 'unknown',
                'operator': 'Opera',
                'driller': 'Blah Exploration Pty Ltd',
                'drillStartDate': '1978-05-28Z',
                'drillEndDate': '1979-05-28Z',
                'startPoint': 'unknown',
                'inclinationType': 'inclined down',
                'boreholeMaterialCustodian': 'blah',
                'boreholeLength_m': '60.3',
                'elevation_m': '791.4',
                'elevation_srs': 'http://www.opengis.net/def/crs/EPSG/0/5711',
		'positionalAccuracy': '1.2',
		'source': 'Src',
                'parentBorehole_uri': 'http://blah.org/blah-d354454546e3esd3454',
                'metadata_uri': 'http://blah.org/geosciml-drillhole-locations-in-blah-d354a70a4a29536166ab8a9ca6470a79d628c05e',
                'genericSymbolizer': 'SSSSS',
                'z': 791.4})

            # Test an almost completely empty borehole
            self.assertEqual(l[5], {'nvcl_id': '12992', 'x': 145.67585285, 'y': -41.61422342, 'href': '', 'name': '', 'description': '', 'purpose': '', 'status': '', 'drillingMethod': '', 'operator': '', 'driller': '', 'drillStartDate': '', 'drillEndDate': '', 'startPoint': '', 'inclinationType': '', 'boreholeMaterialCustodian': '', 'boreholeLength_m': '', 'elevation_m': '', 'elevation_srs': '', 'positionalAccuracy': '', 'source': '', 'parentBorehole_uri': '', 'metadata_uri': '', 'genericSymbolizer': '', 'z': 0.0})

            l = rdr.get_nvcl_id_list()
            self.assertEqual(len(l), 102)
            self.assertEqual(l[0:3], ['10026','10027','10343'])


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_bbox_wfs(self, mock_wfs):
        ''' Test bounding box precision of selecting boreholes
            There are two boreholes in the test data: one is just within
            the bounding box, the other is just outside
        '''
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('bbox_wfs.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
            param_obj = self.setup_param_obj(max_boreholes=0, bbox={"west": 146.0,"south": -41.2,"east": 147.2,"north": -40.5})
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(len(l), 1)
            l = rdr.get_nvcl_id_list()
            self.assertEqual(len(l), 1)


    @unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True)
    def test_bad_coord_wfs(self, mock_wfs):
        ''' Test WFS response with bad coordinates
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        wfs_obj = mock_wfs.return_value
        wfs_obj.getfeature.return_value = Mock()
        with open('badcoord_wfs.txt') as fp:
            wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
            param_obj = self.setup_param_obj()
            with self.assertLogs('nvcl_kit.wfs_helpers', level='WARN') as nvcl_log:
                rdr = NVCLReader(param_obj)
                self.assertTrue(len(nvcl_log.output)>0, "Missing 'Cannot parse collar coordinates'")
                self.assertIn('Cannot parse collar coordinates', nvcl_log.output[0])


    def setup_reader(self):
        ''' Initialises NVCLReader() object

        :returns: NVLKit() object
        '''
        rdr = None
        with unittest.mock.patch('nvcl_kit.reader.WebFeatureService', autospec=True) as mock_wfs:
            wfs_obj = mock_wfs.return_value
            wfs_obj.getfeature.return_value = Mock()
            with open('full_wfs3.txt') as fp:
                wfs_obj.getfeature.return_value.read.return_value = fp.read().rstrip('\n')
                param_obj = self.setup_param_obj()
                rdr = NVCLReader(param_obj)
        return rdr 


    def setup_urlopen(self, fn, params, src_file, binary=False):
        ''' Patches over 'urlopen()' call and calls a function with parameters

        :param fn: function to call
        :param params: function's parameters as a dict
        :param src_file: filename of a file containing data returned from patched 'urlopen()'
        :returns: data returned from function call
        '''
        rdr = self.setup_reader()
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
   

    def test_imagelog_data(self):
        ''' Test get_imagelog_data()
        '''
        imagelog_data_list = self.setup_urlopen('get_imagelog_data', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        self.assertEqual(len(imagelog_data_list), 5)

        self.assertEqual(imagelog_data_list[0].log_id, '2023a603-7b31-4c97-ad59-efb220d93d9')
        self.assertEqual(imagelog_data_list[0].log_name, 'Tray')
        self.assertEqual(imagelog_data_list[0].log_type, '1')
        self.assertEqual(imagelog_data_list[0].algorithmout_id, '0')


    def urllib_exception_tester(self, exc, fn, msg, params):
        ''' Creates an exception in urllib.request.urlopen() read() and
            tests for the correct warning message

        :param exc: exception that is to be created
        :param fn: NVCLReader function to be tested
        :param msg: warning message to test for
        :param params: dictionary of parameters for 'fn'
        '''
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            open_obj.__enter__.return_value.read.side_effect = exc
            open_obj.__enter__.return_value.read.return_value = '' 
            with self.assertLogs('nvcl_kit.svc_interface', level='WARN') as nvcl_log:
                imagelog_data_list = fn(**params)
                self.assertTrue(len(nvcl_log.output)>0, f"Missing '{msg}' in output")
                self.assertIn(msg, nvcl_log.output[0])
    

    def test_imagelog_exception(self):
        ''' Tests exception handling in get_imagelog_data()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_imagelog_data, 'HTTP Error:', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_imagelog_data, 'OS Error:', {'nvcl_id':'dummy-id'})

        
    def test_profilometer_data(self):
        ''' Test get_profilometer_data()
        '''
        prof_data_list = self.setup_urlopen('get_profilometer_data', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        self.assertEqual(len(prof_data_list), 1)

        self.assertEqual(prof_data_list[0].log_id, 'a61b105c-31e8-4da7-b790-4f21c9341c5')
        self.assertEqual(prof_data_list[0].log_name, 'Profile log')
        self.assertEqual(prof_data_list[0].max_val, 78.40174)
        self.assertEqual(prof_data_list[0].min_val, 0.001537323)
        self.assertEqual(prof_data_list[0].floats_per_sample, 128)
        self.assertEqual(prof_data_list[0].sample_count, 30954)


    def test_profilometer_exception(self):
        ''' Tests exception handling in get_profilometer_data()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_profilometer_data, 'HTTP Error:', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_profilometer_data, 'OS Error:', {'nvcl_id':'dummy-id'})


    def test_scalar_logs(self):
        ''' Tests get_scalar_logs()
        '''
        log_list = self.setup_urlopen('get_scalar_logs', {'dataset_id':"blah"}, 'logcoll_scalar.txt')
        self.assertEqual(len(log_list), 4)
        self.assertEqual(log_list[0].log_id, '2023a603-7b31-4c97-ad59-efb220d93d9')
        self.assertEqual(log_list[0].log_name, 'Tray')
        self.assertEqual(log_list[0].is_public, 'true')
        self.assertEqual(log_list[0].log_type, '1')
        self.assertEqual(log_list[0].algorithm_id, '0')


    def test_logs_scalar_empty(self):
        ''' Tests get_scalar_logs() with an empty response
        '''
        rdr = self.setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('logcoll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                log_list = rdr.get_scalar_logs("blah")
                self.assertEqual(len(log_list), 0)


    def test_logs_scalar_exception(self):
        ''' Tests exception handling in get_scalar_logs()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_scalar_logs, 'HTTP Error:', {'dataset_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_scalar_logs, 'OS Error:', {'dataset_id':'dummy-id'})



    def test_mosaic_imglogs(self):
        ''' Tests get_logs_mosaic()
        '''
        log_list = self.setup_urlopen('get_mosaic_imglogs', {'dataset_id':"blah"}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, '5f14ca9c-6d2d-4f86-9759-742dc738736')
        self.assertEqual(log_list[0].log_name, 'Mosaic')
        self.assertEqual(log_list[0].sample_count, 1)


    def test_mosaic_imglogs_empty(self):
        ''' Tests get_mosaic_imglogs() with an empty response
        '''
        rdr = self.setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('logcoll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                log_list = rdr.get_mosaic_imglogs("blah")
                self.assertEqual(len(log_list), 0)


    def test_mosaic_imglogs_exception(self):
        ''' Tests exception handling in get_mosaic_imglogs()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_mosaic_imglogs, 'HTTP Error:', {'dataset_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_mosaic_imglogs, 'OS Error:', {'dataset_id':'dummy-id'})


    def test_datasetid_list(self):
        ''' Test get_datasetid_list()
        '''
        dataset_id_list = self.setup_urlopen('get_datasetid_list', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        self.assertEqual(len(dataset_id_list), 1)
        self.assertEqual(dataset_id_list[0], 'a4c1ed7f-1e87-444a-90ae-3fe5abf9081')


    def test_datasetid_list_empty(self):
        ''' Test get_datasetid_list() with an empty response
        '''
        rdr = self.setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('dataset_coll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                dataset_id_list = rdr.get_datasetid_list("blah")
                self.assertEqual(len(dataset_id_list), 0)


    def test_datasetid_list_exception(self):
        ''' Tests exception handling in get_datasetid_list()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_datasetid_list, 'HTTP Error:', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_datasetid_list, 'OS Error:', {'nvcl_id':'dummy-id'})


    def test_dataset_list(self):
        ''' Test get_dataset_list()
        '''
        dataset_data_list = self.setup_urlopen('get_dataset_list', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        self.assertEqual(len(dataset_data_list), 1)
        ds = dataset_data_list[0]
        self.assertEqual(ds.dataset_id, 'a4c1ed7f-1e87-444a-90ae-3fe5abf9081')
        self.assertEqual(ds.dataset_name, '6315_HP4_Mt_Block')
        self.assertEqual(ds.borehole_uri, 'http://www.blah.blah.gov.au/resource/feature/blah/borehole/6315')
        self.assertEqual(ds.tray_id, '2023a603-7b31-4c97-ad59-efb220d93d9')
        self.assertEqual(ds.section_id, '6c6b3980-8ef3-4d4e-a509-996e4f97973')
        self.assertEqual(ds.domain_id, '1186d6e5-3102-4e60-a077-e17b8ea1079')


    def test_dataset_list_empty(self):
        ''' Test get_dataset_list() with an empty response
        '''
        rdr = self.setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('dataset_coll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                dataset_list = rdr.get_dataset_list("blah")
                self.assertEqual(len(dataset_list), 0)


    def test_dataset_list_exception(self):
        ''' Tests exception handling in get_dataset_list()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_dataset_list, 'HTTP Error:', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_dataset_list, 'OS Error:', {'nvcl_id':'dummy-id'})


    def test_spectrallog_data(self):
        ''' Test get_spectrallog_data()
        '''
        spectral_data_list = self.setup_urlopen('get_spectrallog_data', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        self.assertEqual(len(spectral_data_list), 15)
        self.assertEqual(spectral_data_list[0].log_id, '869f6712-f259-4267-874d-d341dd07bd5')
        self.assertEqual(spectral_data_list[0].log_name, 'Reflectance')
        self.assertEqual(spectral_data_list[0].wavelength_units, 'nm')
        self.assertEqual(spectral_data_list[0].sample_count, 30954)
        self.assertEqual(spectral_data_list[0].script, {'dscl': '0.000000', 'which': '64', 'prenorm': '0', 'postnorm': '0', 'bkrem': '0', 'sgleft': '0', 'sgright': '0', 'sgpoly': '0', 'sgderiv': '0'})
        self.assertEqual(spectral_data_list[0].script_raw, 'dscl=0.000000; which=64; prenorm=0; postnorm=0; bkrem=0; sgleft=0; sgright=0; sgpoly=0; sgderiv=0;')
        self.assertEqual(len(spectral_data_list[0].wavelengths), 531)
        self.assertEqual(spectral_data_list[0].wavelengths[1], 384.0)


    def test_spectrallog_exception(self):
        ''' Tests exception handling in get_spectrallog_data()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_spectrallog_data, 'HTTP Error:', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_spectrallog_data, 'OS Error:', {'nvcl_id':'dummy-id'})


    def test_spectrallog_datasets(self):
        ''' Tests get_spectrallog_datasets()
        '''
        spectral_dataset = self.setup_urlopen('get_spectrallog_datasets', {'log_id':"blah"}, 'spectraldata', binary=True)
        self.assertEqual(spectral_dataset[0], 129)
        self.assertEqual(spectral_dataset[1], 32)
        self.assertEqual(spectral_dataset[2], 206)


    def test_spectrallog_datasets_exception(self):
        ''' Tests exception handling in get_spectrallog_datasets()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_spectrallog_datasets, 'HTTP Error:', {'log_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_spectrallog_datasets, 'OS Error:', {'log_id':'dummy-id'})


    def test_borehole_data(self):
        ''' Test get_borehole_data()
        '''
        bh_data_list = self.setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class"}, 'bh_data.txt')
        self.assertEqual(len(bh_data_list), 28)
        self.assertEqual(isinstance(bh_data_list[5.0], SimpleNamespace), True)

        self.assertEqual(bh_data_list[5.0].className, 'dummy-class')
        self.assertEqual(bh_data_list[5.0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[5.0].colour, (1.0, 1.0, 0.0, 1.0))

        self.assertEqual(bh_data_list[275.0].className, 'dummy-class')
        self.assertEqual(bh_data_list[275.0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[275.0].colour, (1.0, 1.0, 0.0, 1.0))


    def test_borehole_data_top_n(self):
        ''' Test get_borehole_data() with top_n parameter
        '''
        top_n = 2
        bh_data_list = self.setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class", 'top_n': top_n}, 'bh_data.txt')
        self.assertEqual(len(bh_data_list), 28)
        self.assertEqual(len(bh_data_list[5.0]), top_n)
        self.assertEqual(isinstance(bh_data_list[5.0], list), True)

        self.assertEqual(bh_data_list[5.0][0].className, 'dummy-class')
        self.assertEqual(bh_data_list[5.0][0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[5.0][0].colour, (1.0, 1.0, 0.0, 1.0))

        self.assertEqual(bh_data_list[5.0][1].className, 'dummy-class')
        self.assertEqual(bh_data_list[5.0][1].classText, 'KAOLIN')
        self.assertEqual(bh_data_list[5.0][1].colour, (1.0, 0.0, 0.0, 1.0))

        self.assertEqual(len(bh_data_list[275.0]), top_n)

        self.assertEqual(bh_data_list[275.0][0].className, 'dummy-class')
        self.assertEqual(bh_data_list[275.0][0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[275.0][0].colour, (1.0, 1.0, 0.0, 1.0))

        self.assertEqual(bh_data_list[275.0][1].className, 'dummy-class')
        self.assertEqual(bh_data_list[275.0][1].classText, 'CHLORITE')
        self.assertEqual(bh_data_list[275.0][1].colour, (0.0, 1.0, 0.0, 1.0))

    def test_borehole_data_top_n_error(self):
        ''' Test get_borehole_data() with top_n parameter as a negative number
        '''
        top_n = -10
        bh_data_list = self.setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class", 'top_n': top_n}, 'bh_data.txt')
        self.assertEqual(len(bh_data_list), 28)
        self.assertEqual(isinstance(bh_data_list[5.0], SimpleNamespace), True)

        self.assertEqual(bh_data_list[5.0].className, 'dummy-class')
        self.assertEqual(bh_data_list[5.0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[5.0].colour, (1.0, 1.0, 0.0, 1.0))

        self.assertEqual(bh_data_list[275.0].className, 'dummy-class')
        self.assertEqual(bh_data_list[275.0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[275.0].colour, (1.0, 1.0, 0.0, 1.0))


    def test_borehole_exception(self):
        ''' Tests exception handling in get_borehole_data()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_borehole_data, 'HTTP Error:', {'log_id': 'dummy-logid', 'height_resol': 20, 'class_name': 'dummy-class'})
        self.urllib_exception_tester(OSError, rdr.get_borehole_data, 'OS Error:',  {'log_id': 'dummy-logid', 'height_resol': 20, 'class_name': 'dummy-class'})


    def test_image_tray_depth(self):
        ''' Tests that it can parse image tray depth data
        '''
        depth_list = self.setup_urlopen('get_tray_depths', {'log_id': 'dummy_id'}, 'img_tray_depth.txt')
        self.assertEqual(len(depth_list), 50)
        self.assertEqual(depth_list[0].sample_no, '0')
        self.assertEqual(depth_list[0].start_value, '3.00451')
        self.assertEqual(depth_list[0].end_value, '7.603529')
        self.assertEqual(depth_list[3].sample_no, '3')
        self.assertEqual(depth_list[3].start_value, '14.903137')
        self.assertEqual(depth_list[3].end_value, '18.103138')


    def test_get_mosaic_imglogs(self):
        log_list = self.setup_urlopen('get_mosaic_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, '5f14ca9c-6d2d-4f86-9759-742dc738736')
        self.assertEqual(log_list[0].log_name, 'Mosaic')
        self.assertEqual(log_list[0].sample_count, 1)


    def test_get_tray_thumbnail_imglogs(self):
        log_list = self.setup_urlopen('get_tray_thumb_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, '5e6fb391-5fef-4bb0-ae8e-dea25e7958d')
        self.assertEqual(log_list[0].log_name, 'Tray Thumbnail Images')
        self.assertEqual(log_list[0].sample_count, 50)


    def test_get_tray_imglogs(self):
        log_list = self.setup_urlopen('get_tray_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, 'bc79d76a-02ef-44e2-96f2-008a4145cf3')
        self.assertEqual(log_list[0].log_name, 'Tray Images')
        self.assertEqual(log_list[0].sample_count, 50)


    def test_imagery_imglogs(self):
        log_list = self.setup_urlopen('get_imagery_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, 'b80a98e4-6d9b-4a58-ab04-d105c172e67')
        self.assertEqual(log_list[0].log_name, 'Imagery')
        self.assertEqual(log_list[0].sample_count, 30954)


    def test_get_algorithms(self):
        alg_dict = self.setup_urlopen('get_algorithms', {}, 'algorithms.txt')
        self.assertEqual(alg_dict['82'],'703')
        self.assertEqual(alg_dict['6'],'500')
        self.assertEqual(alg_dict['149'],'708')
        
    def test_get_algorithms_exception(self):
        ''' Tests exception handling in get_algorithms()
        '''
        rdr = self.setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_algorithms, 'HTTP Error:', {})
        self.urllib_exception_tester(OSError, rdr.get_algorithms, 'OS Error:', {})


