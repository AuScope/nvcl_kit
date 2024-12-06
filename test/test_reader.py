#!/usr/bin/env python3
import sys, os
import glob
import random
import unittest
import json
import urllib3  # Used for WFS Feature request retries

from unittest.mock import patch, Mock, MagicMock
from requests.exceptions import Timeout, RequestException, ConnectionError, TooManyRedirects
from http.client import HTTPException
import logging
import datetime
from dateutil.tz import tzoffset
from shapely import Polygon, LinearRing

from types import SimpleNamespace

from nvcl_kit.reader import NVCLReader

from helpers import setup_param_obj, setup_reader, setup_urlopen, setup_reqs_obj

MAX_BOREHOLES = 6

'''
Tests for the reader module
'''

class TestNVCLReader(unittest.TestCase):


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get', autospec=True)
    def test_logging_level(self, mock_reqs):
        ''' Test the 'log_lvl' parameter in the constructor
        '''
        reqs_obj = mock_reqs.return_value
        reqs_obj.get.return_value = Mock()
        with open('empty_wfs.json') as fp:
            reqs_obj.get.return_value.read.return_value = fp.readline()
            with self.assertLogs('nvcl_kit.cql_filter', level='DEBUG') as nvcl_log:
                param_obj = SimpleNamespace()
                param_obj.PROV = 'blah'
                param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
                param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
                NVCLReader(param_obj, log_lvl=logging.DEBUG)
                self.assertTrue(len(nvcl_log.output)>0, "Missing ERROR message in output")
                self.assertIn("blah returned error", nvcl_log.output[0])
        

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


    def test_bad_maxbh_param(self):
        ''' Tests that if has a bad 'MAX_BOREHOLES' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.MAX_BOREHOLES = "blah"
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "'MAX_BOREHOLES' parameter is not an integer")


    def test_bad_bbox_param1(self):
        ''' Tests that if has a bad 'BBOX' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BBOX = "blah"
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "'BBOX' parameter is not a dict")


    def test_bad_bbox_param2(self):
        ''' Tests that if it is missing part of 'BBOX' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BBOX = { 'north': 0, 'west':90, 'east':180 }
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "BBOX['south'] parameter is missing")


    def test_bad_bbox_param3(self):
        ''' Tests that if part of 'BBOX' parameter is not a number it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.BBOX = { 'south': '-40', 'north': 0, 'west': 90, 'east':180 }
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "BBOX['south'] parameter is not a number")

    def test_bad_polygon_param(self):
        ''' Tests if 'POLYGON' parameter is not assigned properly, it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.POLYGON = []
        param_obj.PROV = "blah"
        self.try_input_param(param_obj,"'POLYGON' parameter is not a shapely.Polygon")
 
    def test_missing_wfs_param(self):
        ''' Tests that if it is missing 'WFS_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "'WFS_URL' parameter is missing")


    def test_bad_wfs_param(self):
        ''' Tests that if it has a bad 'WFS_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.WFS_URL = None
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "'WFS_URL' parameter is not a string")


    def test_missing_nvcl_param(self):
        ''' Tests that if it is missing 'NVCL_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "'NVCL_URL' parameter is missing")


    def test_bad_nvcl_param(self):
        ''' Tests that if it has a bad 'NVCL_URL' parameter it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = None
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.PROV = "blah"
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
            param_obj.PROV = "blah"
            self.try_input_param(param_obj, err_str)


    def test_bad_use_cql_param(self):
        ''' Tests that if the 'USE_CQL' is a bad value it issues a
            warning message and returns wfs attribute as None
        '''
        param_obj = SimpleNamespace()
        param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
        param_obj.USE_CQL = "True"
        param_obj.WFS_URL = "http://blah.blah.blah/nvcl/geoserver/wfs"
        param_obj.PROV = "blah"
        self.try_input_param(param_obj, "'USE_CQL' parameter is not boolean")


    def wfs_exception_tester(self, mock_reqs, excep, msg):
        ''' Creates an exception in requests get()
            and tests to see that the correct warning message is generated

        :param mock_reqs: mock version of WebFeatureService() object
        :param excep: exception that is to be created
        :param msg: warning message to test for
        '''
        mock_reqs.side_effect = excep
        mock_reqs.return_value.text = ""
        mock_reqs.return_value.status_code = 200
        with self.assertLogs('nvcl_kit.cql_filter', level='WARN') as nvcl_log:
            param_obj = setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            self.assertTrue(len(nvcl_log.output)>0, f"Missing '{msg}' in output")
            self.assertIn(msg, nvcl_log.output[0])
            self.assertEqual(rdr.wfs, None)


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_exception_wfs(self, mock_get):
        ''' Tests that NVCLReader() can handle exceptions in WebFeatureService
            function
        '''
        self.wfs_exception_tester(mock_get, RequestException, 'returned error sending WFS GetFeature')
        self.wfs_exception_tester(mock_get, urllib3.exceptions.HTTPError, 'returned error sending WFS GetFeature')


    def wfs_read_exception_tester(self, mock_reqs, excep, msg):
        ''' Creates an exception in requests get() and tests for the
            correct warning message
        :param mock_reqs: mock version of WebFeatureService() object
        :param excep: exception that is to be created
        :param msg: warning message to test for
        '''
        reqs_obj = mock_reqs.return_value
        mock_reqs.side_effect = excep
        with self.assertLogs('nvcl_kit.cql_filter', level='ERROR') as nvcl_log:
            param_obj = setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertTrue(len(nvcl_log.output)>0, f"Missing '{msg}' in output")
            self.assertIn(msg, nvcl_log.output[0])
            self.assertEqual(rdr.wfs, None)


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_exception_get_read(self, mock_get):
        ''' Tests that it can handle exceptions in requests get() function
        '''
        for excep in [Timeout, RequestException, urllib3.exceptions.HTTPError]:
            self.wfs_read_exception_tester(mock_get, excep, 'returned error sending WFS GetFeature')


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_none_wfs(self, mock_get):
        ''' Test that it does not crash upon 'None', empty string, non-ascii byte string responses
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        bad_byte_str = b'\xff\xff\xff'
        byte_str = b'Test String \xf0\x9f\x98\x80'
        utf_str = byte_str.decode('utf-8')
        for resp in [None, b"", "", byte_str, bad_byte_str, utf_str, []]:
            reqs_obj = mock_get.return_value
            reqs_obj = setup_reqs_obj(resp, reqs_obj)
            param_obj = setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(l, [])
            l = rdr.get_nvcl_id_list()
            self.assertEqual(l, [])
            # Check that read() is called once only
            if hasattr(reqs_obj, 'assert_called_once'):
                reqs_obj.read.assert_called_once()


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_empty_wfs(self, mock_get):
        ''' Test empty but valid WFS response
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        reqs_obj = mock_get.return_value
        with open('empty_wfs.json') as fp:
            reqs_obj, json_obj = setup_reqs_obj(fp, reqs_obj)
            param_obj = setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(l, [])
            l = rdr.get_nvcl_id_list()
            self.assertEqual(l, [])
            # Check that read() is called once only
            if hasattr(reqs_obj.json, 'assert_called_once'):
                reqs_obj.json.assert_called_once()


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_max_bh_wfs(self, mock_get):
        ''' Test full WFS response, maximum number of boreholes is enforced
            (tests get_boreholes_list() & get_nvcl_id_list() )
        '''
        reqs_obj = mock_get.return_value
        with open('full_wfs_cql.json') as fp:
            reqs_obj, json_obj = setup_reqs_obj(fp, reqs_obj)
            param_obj = setup_param_obj(max_boreholes=MAX_BOREHOLES)
            rdr = NVCLReader(param_obj)
            l = rdr.get_boreholes_list()
            self.assertEqual(len(l), MAX_BOREHOLES)
            l = rdr.get_nvcl_id_list()
            self.assertEqual(len(l), MAX_BOREHOLES)


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_all_bh_wfs_cql(self, mock_get):
        ''' Test full WFS response from CQL_FILTER request, unlimited number of boreholes
        '''
        reqs_obj = mock_get.return_value
        with open('full_wfs_cql.json') as fp:
            reqs_obj, json_obj = setup_reqs_obj(fp, reqs_obj)
            feat_len = len(json_obj["features"])

            param_obj = setup_param_obj()
            rdr = NVCLReader(param_obj)
            bhs = rdr.get_boreholes_list()
            # Check that number passed in == number fetched
            self.assertEqual(len(bhs), feat_len)
            # Test with all fields having values
            should_be = SimpleNamespace(**{
                "identifier":"https://gs.geoscience.nsw.gov.au/resource/feature/gsnsw/borehole/MIN_305246",
	            "nvcl_id":"MIN_305246",
                "x":147.93071504,
                "y":-35.12615836,
                "z":290,
                "href":"https://gs.geoscience.nsw.gov.au/resource/feature/gsnsw/borehole/MIN_305246",
                "name":"Mundarlo: MURC004",
                "description":"Metallic minerals",
                "purpose": "any purpose",
                "status": "any status",
                "drillingMethod":"diamond drill",
                "operator":"Mclatchie",
                "driller":"any driller",
                "drillStartDate":"2018",
                "drillEndDate":"2018",
                "startPoint":"any startPoint",
                "inclinationType":"any inclinationType",
                "boreholeMaterialCustodian":"any custodian",
                "boreholeLength_m":"519.6",
                "elevation_m":"290",
                "elevation_srs":"EPSG:1234",
                "positionalAccuracy":"positional accuracy",
                "source":"NSW Geoscientific Data Warehouse",
                "parentBorehole_uri":"borehole URI",
                "metadata_uri":"https://geonetwork.geoscience.nsw.gov.au/geonetwork/srv/eng/catalog.search#/metadata/0ba7fe4639b8b9a073ef3e8ea82a29b31a171162",
                "genericSymbolizer":"unknown",
                "project":"Mundarlo",
                "tenement":"EL8096"})
            self.assertEqual(bhs[5], should_be)

            # Test an almost completely empty borehole
            should_be = SimpleNamespace(**{
                'identifier':'', 'nvcl_id': 'MIN_138214', 'x': 147.91664131, 'y':-35.1982468, 'href': '', 'name': '', 'description': '', 'purpose': '', 'status': '', 'drillingMethod': '', 'operator': '', 'driller': '', 'drillStartDate': '', 'drillEndDate': '', 'startPoint': '', 'inclinationType': '', 'boreholeMaterialCustodian': '', 'boreholeLength_m': '0.0', 'elevation_m': '0.0', 'elevation_srs': '', 'positionalAccuracy': '', 'source': '', 'parentBorehole_uri': '', 'metadata_uri': '', 'genericSymbolizer': '', 'z': 0.0, 'tenement':'', 'project':''})
            self.assertEqual(bhs[4], should_be)

            # Test fetching borehole ids
            ids = rdr.get_nvcl_id_list()
            self.assertEqual(len(ids), 6)
            self.assertEqual(ids[0:3], ['MIN_007619', 'MIN_007633', 'MIN_007637'])


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_all_bh_wfs_xml(self, mock_get):
        ''' Test minimal WFS response, XML FILTER reasponse, unlimited number of boreholes
        '''
        reqs_obj = mock_get.return_value
        with open('full_wfs_xml.json') as fp:
            reqs_obj, json_obj = setup_reqs_obj(fp, reqs_obj)
            feat_len = len(json_obj["features"])

            param_obj = setup_param_obj(use_cql=False)
            rdr = NVCLReader(param_obj)
            bhs = rdr.get_boreholes_list()
            # Check that number passed in == number fetched
            self.assertEqual(len(bhs), feat_len)
            # Test with minimal fields having values
            should_be = SimpleNamespace(**{
                "identifier":"http://geology.data.nt.gov.au/resource/feature/ntgs/borehole/1113668_ECD12",
	            "nvcl_id":"1113668_ECD12",
                "x":131.33847,
                "y":-22.37914,
                "z":0.0,
                "href":"http://geology.data.nt.gov.au/resource/feature/ntgs/borehole/1113668_ECD12",
                "name":"ECD12",
                "drillingMethod":"Diamond Drill",
                "operator":"",
                "driller":"Unknown",
                "drillStartDate":"",
                "drillEndDate":"",
                "description":"",
                "purpose":"",
                "status":"",
                "source":"",
                "parentBorehole_uri":"",
                "elevation_m":"",
                "startPoint":"other: unknown",
                "inclinationType":"vertical",
                "boreholeMaterialCustodian":"Northern Territory Geological Survey",
                "boreholeLength_m":"175.8",
                "elevation_srs":"EPSG:5711",
                "positionalAccuracy":"",
                "status":"",
                "metadata_uri":"http://researchdata.ands.org.au/nvcl-borehole",
                "genericSymbolizer":"",
                "tenement":"",
                "project":""
                })
            self.assertEqual(bhs[5], should_be)

            # Test fetching borehole ids
            ids = rdr.get_nvcl_id_list()
            self.assertEqual(len(ids), 141)
            self.assertEqual(ids[:3], ['1108848_DD95RC128', '1113632_DD85GL5', '1113636_DD85GL6'])


    @unittest.mock.patch('nvcl_kit.cql_filter.requests.Session.get')
    def test_cache(self, mock_get):
        ''' Test CACHE_PATH option
            Tests for existence of both forms of the cache file
        '''
        temp_short = 'tmp-' + ''.join([chr(random.randint(65, 90)) for x in range(10) ])
        temp_long = 'tmp-' + ''.join([chr(random.randint(65, 90)) for x in range(100) ])
        with open('full_wfs_cql.json') as fp:
            for cache_path, tmp_file in [
                               # Test when parameters are incorporated in filename
                               (temp_short, temp_short + 'https%3A%2F%2Fblah.blah.blah%2Fnvcl%2FNVCLDataServices%2FgetDownsampledData.html%3Flogid%3Ddummy-id%26interval%3D10.0%26outputformat%3Djson%26startdepth%3D0.0%26enddepth%3D10000.0.txt'),
                               # Test when parameters are hashed because filename is too long
                               (temp_long, temp_long + 'https%3A%2F%2Fblah.blah.blah%2Fnvcl%2FNVCLDataServices%2FgetDownsampledData.html%3F6024443c534411d094f0cc87b78b708c2c7f4b14.txt')]:
                reqs_obj = mock_get.return_value
                reqs_obj = setup_reqs_obj(fp, reqs_obj)
                # Setup params for NVCLReader() with CACHE_PATH set
                param_obj = setup_param_obj(max_boreholes=0, cache_path=cache_path)
                rdr = NVCLReader(param_obj)
                # Calls '_get_response_str()' which will create a cache file
                setup_urlopen('get_borehole_data',
                              {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class"},
                              'bh_data.txt',
                              rdr=rdr)
                # Test for existence of cache file
                dir_list = glob.glob("tmp-*")
                self.assertEqual(dir_list[0], tmp_file)
                self.assertEqual(len(dir_list), 1)
                # Remove cache file
                os.remove(tmp_file)


    def test_imagelog_data(self):
        ''' Test get_imagelog_data()
        '''
        imagelog_data_list = setup_urlopen('get_imagelog_data', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        # Tests fetching and parsing '<ImageLog>' elements
        self.assertEqual(len(imagelog_data_list), 4)
        self.assertEqual(imagelog_data_list[0].log_id, '5f14ca9c-6d2d-4f86-9759-742dc738736')
        self.assertEqual(imagelog_data_list[0].log_name, 'Mosaic')
        self.assertEqual(imagelog_data_list[0].sample_count, '1')
        self.assertFalse(hasattr(imagelog_data_list[0], 'created_date'))
        self.assertFalse(hasattr(imagelog_data_list[0], 'modified_date'))

    
    def test_imagelog_data_time(self):
        ''' Test get_imagelog_data() time parsing
        '''
        imagelog_data_list = setup_urlopen('get_imagelog_data', {'nvcl_id':"blah"}, 'dataset_coll_time.txt')
        # Tests fetching and parsing text in '<createdDate>' and '<modifiedDate>' elements
        self.assertEqual(len(imagelog_data_list), 4)
        self.assertEqual(imagelog_data_list[0].created_date, datetime.datetime(2022, 9, 13, 14, 38, 24, tzinfo=tzoffset(None, 34200)))
        self.assertEqual(imagelog_data_list[0].modified_date, datetime.datetime(2022, 9, 14, 14, 38, 39, tzinfo=tzoffset(None, 34200)))


    def test_imagelog_data_time_bad(self):
        ''' Test get_imagelog_data() bad time parsing
        '''
        imagelog_data_list = setup_urlopen('get_imagelog_data', {'nvcl_id':"blah"}, 'dataset_coll_time_bad.txt')
        # Tests badly formatted text in '<modifiedDate>' element
        self.assertFalse(hasattr(imagelog_data_list[0], 'modified_date'))


    def test_imagelog_exception(self):
        ''' Tests exception handling in get_imagelog_data()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_imagelog_data, 'HTTP Error with', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_imagelog_data, 'OS Error with', {'nvcl_id':'dummy-id'})


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
    
    def test_get_logs_data(self):
        ''' Test the generic get_logs_data()
        '''
        bh_data_list = setup_urlopen('get_logs_data', {'nvcl_id':"dummy-id"}, 'dataset_coll.txt')
        self.assertEqual(len(bh_data_list), 70)
        self.assertEqual(isinstance(bh_data_list[0], SimpleNamespace), True)

        self.assertEqual(bh_data_list[0].algorithm_id, '0')
        self.assertEqual(bh_data_list[0].is_public, 'true')
        self.assertEqual(bh_data_list[0].log_id, '2023a603-7b31-4c97-ad59-efb220d93d9')
        self.assertEqual(bh_data_list[0].log_name, 'Tray')
        self.assertEqual(bh_data_list[0].log_type, '1')

    def test_get_logs_data_empty(self):
        ''' Test the generic get_logs_data()
        '''
        bh_data_list = setup_urlopen('get_logs_data', {'nvcl_id':"dummy-id"}, 'dataset_coll_empty.txt')
        self.assertEqual(len(bh_data_list), 0)

    def test_get_logs_exception(self):
        ''' Tests exception handling in get_logs_data()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_logs_data, 'HTTP Error with', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_logs_data, 'OS Error with', {'nvcl_id':'dummy-id'})

    def test_get_logs_time(self):
        ''' Tests time retrieval in get_logs_data()
        '''
        bh_data_list = setup_urlopen('get_logs_data', {'nvcl_id':"dummy-id"}, 'dataset_coll_time.txt')
        self.assertEqual(isinstance(bh_data_list[0], SimpleNamespace), True)
        self.assertEqual(bh_data_list[2].created_date, datetime.datetime(2022, 9, 13, 14, 38, 24, tzinfo=tzoffset(None, 34200)))
        self.assertEqual(bh_data_list[2].modified_date, datetime.datetime(2022, 9, 14, 14, 38, 39, tzinfo=tzoffset(None, 34200)))

    def test_get_logs_badtime(self):
        ''' Tests badly formatted time retrieval in get_logs_data()
        '''
        bh_data_list = setup_urlopen('get_logs_data', {'nvcl_id':"dummy-id"}, 'dataset_coll_time_bad.txt')
        self.assertEqual(isinstance(bh_data_list[0], SimpleNamespace), True)
        self.assertFalse(hasattr(bh_data_list[0], 'modified_date'))

    def test_profilometer_data(self):
        ''' Test get_profilometer_data()
        '''
        prof_data_list = setup_urlopen('get_profilometer_data', {'nvcl_id':"blah"}, 'dataset_coll.txt')
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
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_profilometer_data, 'HTTP Error with', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_profilometer_data, 'OS Error with', {'nvcl_id':'dummy-id'})

    def test_profilometer_datasets(self):
        ''' Tests fetching profilometer datasets
        '''
        prof_dataset_list = setup_urlopen('get_profilometer_datasets', {'proflog_id':"blah"}, 'profilometer_data.json')
        self.assertEqual(prof_dataset_list[0].sampleNo, 0)
        self.assertEqual(prof_dataset_list[0].floatprofdata[3], 33.821205)
        self.assertEqual(prof_dataset_list[41387].sampleNo, 41387)
        self.assertEqual(prof_dataset_list[41387].floatprofdata[19], 0.006286621)

    def test_profilometer_datasets_exception(self):
        ''' Tests fetching profilometer datasets exception handling
        '''
        prof_dataset_list = setup_urlopen('get_profilometer_datasets', {'proflog_id':"blah"}, 'error_page.html')
        self.assertEqual(prof_dataset_list, [])

    def test_scalar_logs(self):
        ''' Tests get_scalar_logs()
        '''
        log_list = setup_urlopen('get_scalar_logs', {'dataset_id':"blah"}, 'logcoll_scalar.txt')
        self.assertEqual(len(log_list), 4)
        self.assertEqual(log_list[0].log_id, '2023a603-7b31-4c97-ad59-efb220d93d9')
        self.assertEqual(log_list[0].log_name, 'Tray')
        self.assertEqual(log_list[0].is_public, 'true')
        self.assertEqual(log_list[0].log_type, '1')
        self.assertEqual(log_list[0].algorithm_id, '0')


    def test_logs_scalar_empty(self):
        ''' Tests get_scalar_logs() with an empty response
        '''
        rdr = setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('logcoll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                log_list = rdr.get_scalar_logs("blah")
                self.assertEqual(len(log_list), 0)


    def test_logs_scalar_exception(self):
        ''' Tests exception handling in get_scalar_logs()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_scalar_logs, 'HTTP Error with', {'dataset_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_scalar_logs, 'OS Error with', {'dataset_id':'dummy-id'})



    def test_mosaic_imglogs(self):
        ''' Tests get_logs_mosaic()
        '''
        log_list = setup_urlopen('get_mosaic_imglogs', {'dataset_id':"blah"}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, '5f14ca9c-6d2d-4f86-9759-742dc738736')
        self.assertEqual(log_list[0].log_name, 'Mosaic')
        self.assertEqual(log_list[0].sample_count, 1)


    def test_mosaic_imglogs_empty(self):
        ''' Tests get_mosaic_imglogs() with an empty response
        '''
        rdr = setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('logcoll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                log_list = rdr.get_mosaic_imglogs("blah")
                self.assertEqual(len(log_list), 0)


    def test_mosaic_imglogs_exception(self):
        ''' Tests exception handling in get_mosaic_imglogs()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_mosaic_imglogs, 'HTTP Error with', {'dataset_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_mosaic_imglogs, 'OS Error with', {'dataset_id':'dummy-id'})


    def test_datasetid_list(self):
        ''' Test get_datasetid_list()
        '''
        dataset_id_list = setup_urlopen('get_datasetid_list', {'nvcl_id':"blah"}, 'dataset_coll.txt')
        self.assertEqual(len(dataset_id_list), 1)
        self.assertEqual(dataset_id_list[0], 'a4c1ed7f-1e87-444a-90ae-3fe5abf9081')


    def test_datasetid_list_empty(self):
        ''' Test get_datasetid_list() with an empty response
        '''
        rdr = setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('dataset_coll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                dataset_id_list = rdr.get_datasetid_list("blah")
                self.assertEqual(len(dataset_id_list), 0)


    def test_datasetid_list_exception(self):
        ''' Tests exception handling in get_datasetid_list()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_datasetid_list, 'HTTP Error with', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_datasetid_list, 'OS Error with', {'nvcl_id':'dummy-id'})


    def test_dataset_list(self):
        ''' Test get_dataset_list()
        '''
        dataset_data_list = setup_urlopen('get_dataset_list', {'nvcl_id':"blah"}, 'dataset_coll.txt')
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
        rdr = setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('dataset_coll_empty.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                dataset_list = rdr.get_dataset_list("blah")
                self.assertEqual(len(dataset_list), 0)


    def test_dataset_list_time(self):
        ''' Test get_dataset_list() with modified time in response
        '''
        rdr = setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('dataset_coll_time.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                dataset_list = rdr.get_dataset_list("blah")
                self.assertEqual(len(dataset_list), 1)
                self.assertEqual(dataset_list[0].created_date, datetime.datetime(2022, 9, 13, 14, 38, 24, tzinfo=tzoffset(None, 34200)))
                self.assertEqual(dataset_list[0].modified_date, datetime.datetime(2022, 9, 14, 14, 38, 39, tzinfo=tzoffset(None, 34200)))


    def test_dataset_list_time_bad(self):
        ''' Test get_dataset_list() with bad modified time in response
        '''
        rdr = setup_reader()
        with unittest.mock.patch('urllib.request.urlopen', autospec=True) as mock_request:
            open_obj = mock_request.return_value
            with open('dataset_coll_time_bad.txt') as fp:
                open_obj.__enter__.return_value.read.return_value = fp.read()
                dataset_list = rdr.get_dataset_list("blah")
                self.assertEqual(len(dataset_list), 1)
                self.assertFalse(hasattr(dataset_list[0], 'modified_date'))


    def test_dataset_list_exception(self):
        ''' Tests exception handling in get_dataset_list()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_dataset_list, 'HTTP Error with', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_dataset_list, 'OS Error with', {'nvcl_id':'dummy-id'})


    def test_spectrallog_data(self):
        ''' Test get_spectrallog_data()
        '''
        spectral_data_list = setup_urlopen('get_spectrallog_data', {'nvcl_id':"blah"}, 'dataset_coll.txt')
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
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_spectrallog_data, 'HTTP Error with', {'nvcl_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_spectrallog_data, 'OS Error with', {'nvcl_id':'dummy-id'})


    def test_spectrallog_datasets(self):
        ''' Tests get_spectrallog_datasets()
        '''
        spectral_dataset = setup_urlopen('get_spectrallog_datasets', {'log_id':"blah"}, 'spectraldata', binary=True)
        self.assertEqual(spectral_dataset[0], 129)
        self.assertEqual(spectral_dataset[1], 32)
        self.assertEqual(spectral_dataset[2], 206)


    def test_spectrallog_datasets_exception(self):
        ''' Tests exception handling in get_spectrallog_datasets()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_spectrallog_datasets, 'HTTP Error with', {'log_id':'dummy-id'})
        self.urllib_exception_tester(OSError, rdr.get_spectrallog_datasets, 'OS Error with', {'log_id':'dummy-id'})


    def test_borehole_data(self):
        ''' Test get_borehole_data()
        '''
        bh_data_list = setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class"}, 'bh_data.txt')
        self.assertEqual(len(bh_data_list), 28)
        self.assertEqual(isinstance(bh_data_list[5.0], SimpleNamespace), True)

        self.assertEqual(bh_data_list[5.0].className, 'dummy-class')
        self.assertEqual(bh_data_list[5.0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[5.0].colour, (1.0, 1.0, 0.0, 1.0))

        self.assertEqual(bh_data_list[275.0].className, 'dummy-class')
        self.assertEqual(bh_data_list[275.0].classText, 'WHITE-MICA')
        self.assertEqual(bh_data_list[275.0].colour, (1.0, 1.0, 0.0, 1.0))

    def test_borehole_data_noclasses(self):
        ''' Test get_borehole_data() with data which has no mineral class data, it should not crash and return no data
        '''
        bh_data_list = setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class"}, 'bh_data_avgval.txt')
        self.assertEqual(len(bh_data_list), 0)


    def test_borehole_data_top_n(self):
        ''' Test get_borehole_data() with top_n parameter
        '''
        top_n = 2
        bh_data_list = setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class", 'top_n': top_n}, 'bh_data.txt')
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
        bh_data_list = setup_urlopen('get_borehole_data', {'log_id':"dummy-id", 'height_resol':10.0, 'class_name':"dummy-class", 'top_n': top_n}, 'bh_data.txt')
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
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_borehole_data, 'HTTP Error with', {'log_id': 'dummy-logid', 'height_resol': 20, 'class_name': 'dummy-class'})
        self.urllib_exception_tester(OSError, rdr.get_borehole_data, 'OS Error with',  {'log_id': 'dummy-logid', 'height_resol': 20, 'class_name': 'dummy-class'})


    def test_image_tray_depth(self):
        ''' Tests that it can parse image tray depth data
        '''
        depth_list = setup_urlopen('get_tray_depths', {'log_id': 'dummy_id'}, 'img_tray_depth.txt')
        self.assertEqual(len(depth_list), 50)
        self.assertEqual(depth_list[0].sample_no, '0')
        self.assertEqual(depth_list[0].start_value, '3.00451')
        self.assertEqual(depth_list[0].end_value, '7.603529')
        self.assertEqual(depth_list[3].sample_no, '3')
        self.assertEqual(depth_list[3].start_value, '14.903137')
        self.assertEqual(depth_list[3].end_value, '18.103138')


    def test_get_mosaic_imglogs(self):
        ''' Tests 'get_mosaic_imglogs' API
        '''
        log_list = setup_urlopen('get_mosaic_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, '5f14ca9c-6d2d-4f86-9759-742dc738736')
        self.assertEqual(log_list[0].log_name, 'Mosaic')
        self.assertEqual(log_list[0].sample_count, 1)


    def test_get_tray_thumbnail_imglogs(self):
        ''' Tests 'get_tray_thumbnail_imglogs' API
        '''
        log_list = setup_urlopen('get_tray_thumb_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, '5e6fb391-5fef-4bb0-ae8e-dea25e7958d')
        self.assertEqual(log_list[0].log_name, 'Tray Thumbnail Images')
        self.assertEqual(log_list[0].sample_count, 50)


    def test_get_tray_imglogs(self):
        ''' Tests 'get_tray_imglogs' API
        '''
        log_list = setup_urlopen('get_tray_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, 'bc79d76a-02ef-44e2-96f2-008a4145cf3')
        self.assertEqual(log_list[0].log_name, 'Tray Images')
        self.assertEqual(log_list[0].sample_count, 50)


    def test_imagery_imglogs(self):
        ''' Tests 'get_imagery_imglogs' API
        '''
        log_list = setup_urlopen('get_imagery_imglogs', {'dataset_id':'dummy-id'}, 'logcoll_mosaic.txt')
        self.assertEqual(len(log_list), 1)
        self.assertEqual(log_list[0].log_id, 'b80a98e4-6d9b-4a58-ab04-d105c172e67')
        self.assertEqual(log_list[0].log_name, 'Imagery')
        self.assertEqual(log_list[0].sample_count, 30954)


    def test_get_algorithms(self):
        ''' Tests 'get_algorithms' API
        '''
        alg_dict = setup_urlopen('get_algorithms', {}, 'algorithms.txt')
        self.assertEqual(alg_dict['82'],'703')
        self.assertEqual(alg_dict['6'],'500')
        self.assertEqual(alg_dict['149'],'708')
        
    def test_get_algorithms_exception(self):
        ''' Tests exception handling in get_algorithms()
        '''
        rdr = setup_reader()
        self.urllib_exception_tester(HTTPException, rdr.get_algorithms, 'HTTP Error with', {})
        self.urllib_exception_tester(OSError, rdr.get_algorithms, 'OS Error with', {})

    def test_filter_feat_list(self):
        ''' Tests 'filter_feat_list' API
        '''
        rdr = setup_reader()
        f_list = rdr.filter_feat_list(name=['Mundarlo: MURC004', 'Mount Adrah: GG12'])
        assert(len(f_list) == 2)
        assert(f_list[0].name == 'Mount Adrah: GG12')
        assert(f_list[1].name == 'Mundarlo: MURC004')

    def test_filter_feat_list_single(self):
        ''' Tests 'filter_feat_list' API
        '''
        rdr = setup_reader()
        f_list = rdr.filter_feat_list(name='Mundarlo: MURC004')
        assert(len(f_list) == 1)
        assert(f_list[0].name == 'Mundarlo: MURC004')

    def test_filter_feat_list_ids_only(self):
        ''' Tests 'filter_feat_list' API, with 'nvcl_ids_only' keyword
        '''
        rdr = setup_reader()
        id_list = rdr.filter_feat_list(nvcl_ids_only=True, name=['Mundarlo: MURC004', 'Mount Adrah: GG12'])
        assert(len(id_list) == 2)
        assert(id_list[0] == 'MIN_007619')
        assert(id_list[1] == 'MIN_305246')

    def test_filter_feat_list_ids_only_single(self):
        ''' Tests 'filter_feat_list' API, with 'nvcl_ids_only' keyword and single value
        '''
        rdr = setup_reader()
        id_list = rdr.filter_feat_list(nvcl_ids_only=True, name='Mundarlo: MURC004')
        assert(len(id_list) == 1)
        assert(id_list[0] == 'MIN_305246')
