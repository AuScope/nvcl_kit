"""
This module is the main interface used to NVCL borehole data from the NVCL services..
"""

import sys

import xml.etree.ElementTree as ET
import json
from collections import OrderedDict
import itertools
import logging
from types import SimpleNamespace

from requests.exceptions import RequestException

from owslib.wfs import WebFeatureService
from owslib.fes import PropertyIsLike, etree
from owslib.util import ServiceException

from http.client import HTTPException

from shapely.geometry.polygon import LinearRing, Point

from nvcl_kit.svc_interface import _ServiceInterface

ENFORCE_IS_PUBLIC = True
''' Enforce the 'is_public' flag , i.e. any data with 'is_public' set to 'false'
    will be ignored
'''

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

TIMEOUT = 6000
''' Timeout for querying WFS and NVCL services (seconds)
'''

MAX_DEPTH = 10000.0
''' Default maximum depth to search for boreholes
'''

MIN_DEPTH = 0.0
''' Default minimum depth to search for boreholes
'''


def bgr2rgba(bgr):
    ''' Converts BGR colour integer into an RGB tuple

    :param bgr: BGR colour integer
    :returns: RGBA float tuple
    '''
    return ((bgr & 255) / 255.0, ((bgr & 65280) >> 8) / 255.0, (bgr >> 16) / 255.0, 1.0)


class NVCLReader:
    ''' A class to extract NVCL borehole data (see README.md for details)
    '''

    def __init__(self, param_obj, wfs=None, log_lvl=None):
        '''
        :param param_obj: SimpleNamespace() object with parameters.
          Fields are:

            * NVCL_URL - URL of NVCL service
            * WFS_URL - URL of WFS service, GeoSciML V4.1 BoreholeView
            * WFS_VERSION - (optional - default "1.1.0")
            * BOREHOLE_CRS - (optional - default "EPSG:4326")
            * DEPTHS - (optional) Tuple of range of depths (min,max) [metres]
            * POLYGON - (optional) 2D 'shapely.geometry.LinearRing' object, only boreholes within this ring are retrieved
            * BBOX - (optional - default {"west": -180.0,"south": -90.0,"east": 180.0,"north": 0.0}) 2D bounding box in EPSG:4326, only boreholes within box are retrieved
            * MAX_BOREHOLES - (optional - default 0) Maximum number of boreholes to retrieve. If < 1 then all boreholes are loaded

          ::

              e.g.
              from types import SimpleNamespace
              from shapely.geometry.polygon import LinearRing
              param_obj = SimpleNamespace()
              # Uses EPSG:4326
              param_obj.BBOX = { "west": 132.76, "south": -28.44, "east": 134.39, "north": -26.87 }
              # Or use a POLYGON instead of a BBOX
              param_obj.POLYGON = LinearRing([(132.76, -28.44), (132.76, -26.87), (134.39, -26.87), (134.39, -28.44), (132.76, -28.44)])
              param_obj.DEPTHS = (100.0, 900.0)
              param_obj.WFS_URL = "http://blah.blah.blah/geoserver/wfs"
              param_obj.NVCL_URL = "https://blah.blah.blah/nvcl/NVCLDataServices"
              param_obj.MAX_BOREHOLES = 20

        :param wfs: optional owslib 'WebFeatureService' object
        :param log_lvl: optional logging level (see 'logging' package),
                        default is logging.INFO

        **NOTE: Check if 'wfs' is not 'None' to see if this instance initialised properly**

        '''
        # Set log level
        if log_lvl and isinstance(log_lvl, int):
            LOGGER.setLevel(log_lvl)
        self.wfs = None
        self.borehole_list = []

        # Check param_obj
        if not isinstance(param_obj, SimpleNamespace):
            LOGGER.warning("'param_obj' is not a SimpleNamespace() object")
            return
        self.param_obj = param_obj

        # Check POLYGON value
        if hasattr(self.param_obj, 'POLYGON'):
            if not isinstance(self.param_obj.POLYGON, LinearRing):
                LOGGER.warning("'POLYGON' parameter is not a shapely.geometry.polygon.LinearRing")
                return

        # Check BBOX value
        elif hasattr(self.param_obj, 'BBOX'):
            if not isinstance(self.param_obj.BBOX, dict):
                LOGGER.warning("'BBOX' parameter is not a dict")
                return

            # Check BBOX dict values
            for dir in ["west", "south", "east", "north"]:
                if dir not in self.param_obj.BBOX:
                    LOGGER.warning("BBOX['%s'] parameter is missing", dir)
                    return
                if not isinstance(self.param_obj.BBOX[dir], float) and \
                   not isinstance(self.param_obj.BBOX[dir], int):
                    LOGGER.warning("BBOX['%s'] parameter is not a number", dir)
                    return
        else:
            # If neither BBOX nor POLYGON is defined, use default BBOX
            self.param_obj.BBOX = {"west": -180.0, "south": -90.0, "east": 180.0, "north": 0.0}

        # Check DEPTHS parameter
        if hasattr(self.param_obj, "DEPTHS"):
            depths = self.param_obj.DEPTHS
            if not isinstance(depths, tuple):
                LOGGER.warning("'DEPTHS' parameter is not a tuple")
                return
            if len(depths) != 2:
                LOGGER.warning("'DEPTHS' parameter does not have length of 2")
                return
            if type(depths[0]) not in [int, float] or type(depths[1]) not in [int, float]:
                LOGGER.warning("'DEPTHS' parameter does not contain numerics")
                return
            if depths[0] >= depths[1]:
                LOGGER.warning("'DEPTHS' parameter minimum is not less then maximum")
                return
            self.min_depth = depths[0]
            self.max_depth = depths[1]
        else:
            self.min_depth = MIN_DEPTH
            self.max_depth = MAX_DEPTH

        # Check WFS_URL value
        if not hasattr(self.param_obj, 'WFS_URL'):
            LOGGER.warning("'WFS_URL' parameter is missing")
            return
        if not isinstance(self.param_obj.WFS_URL, str):
            LOGGER.warning("'WFS_URL' parameter is not a string")
            return

        # Check NVCL_URL value
        if not hasattr(self.param_obj, 'NVCL_URL'):
            LOGGER.warning("'NVCL_URL' parameter is missing")
            return
        if not isinstance(self.param_obj.NVCL_URL, str):
            LOGGER.warning("'NVCL_URL' parameter is not a string")
            return

        # Roughly check BOREHOLE_CRS EPSG: value
        if not hasattr(self.param_obj, 'BOREHOLE_CRS'):
            self.param_obj.BOREHOLE_CRS = "EPSG:4326"   # "EPSG:4283"
        elif (not isinstance(self.param_obj.BOREHOLE_CRS, str) or
              "EPSG:" not in self.param_obj.BOREHOLE_CRS.upper() or
              not self.param_obj.BOREHOLE_CRS[-4:].isnumeric()):
            LOGGER.warning("'BOREHOLE_CRS' parameter is not an EPSG string")
            return

        # Roughly check WFS_VERSION value
        if not hasattr(self.param_obj, 'WFS_VERSION'):
            self.param_obj.WFS_VERSION = "1.1.0"
        elif not isinstance(self.param_obj.WFS_VERSION, str) or not self.param_obj.WFS_VERSION[0].isdigit():
            LOGGER.warning("'WFS_VERSION' parameter is not a numeric string")
            return

        # Check MAX_BOREHOLES value
        if not hasattr(self.param_obj, 'MAX_BOREHOLES'):
            self.param_obj.MAX_BOREHOLES = 0
        if not isinstance(self.param_obj.MAX_BOREHOLES, int):
            LOGGER.warning("'MAX_BOREHOLES' parameter is not an integer")
            return

        # Check USE_LOCAL_FILTERING
        if not hasattr(self.param_obj, 'USE_LOCAL_FILTERING'):
            self.param_obj.USE_LOCAL_FILTERING = False
        if not isinstance(self.param_obj.USE_LOCAL_FILTERING, bool):
            LOGGER.warning("'USE_LOCAL_FILTERING' parameter is not boolean")
            return

        # If owslib wfs is not supplied
        if wfs is None:
            try:
                self.wfs = WebFeatureService(self.param_obj.WFS_URL,
                                             version=self.param_obj.WFS_VERSION,
                                             xml=None, timeout=TIMEOUT)
            except ServiceException as se_exc:
                LOGGER.warning("WFS error: %s", str(se_exc))
            except RequestException as re_exc:
                LOGGER.warning("Request error: %s", str(re_exc))
            except HTTPException as he_exc:
                LOGGER.warning("HTTP error code returned: %s", str(he_exc))
            except OSError as os_exc:
                LOGGER.warning("OS Error: %s", str(os_exc))
        else:
            self.wfs = wfs
        if self.wfs and not self._fetch_borehole_list():
            self.wfs = None

        self.svc = _ServiceInterface(self.param_obj.NVCL_URL, TIMEOUT)

    def get_borehole_data(self, log_id, height_resol, class_name, top_n=1):
        ''' Retrieves borehole mineral data for a borehole

        :param log_id: borehole log identifier, string e.g. 'ce2df1aa-d3e7-4c37-97d5-5115fc3c33d' This is the first id from the list of triplets [log id, log type, log name] fetched from 'get_imagelog_data()'
        :param height_resol: height resolution, float
        :param class_name: name of scalar class, returned in output for informational purposes
        :param top_n: optional number
        :returns: dict: key - depth, float; value - if top_n=1 then  SimpleNamespace( 'colour'= RGBA float tuple, 'className'= class name, 'classText'= mineral name ) & if top_n>1 then [ SimpleNamespace(..) .. ]
        '''
        LOGGER.debug(" get_borehole_data(%s, %d, %s, %d)", log_id, height_resol, class_name, top_n)
        # Check top_n parameter
        if top_n < 1:
            LOGGER.warning("top_n parameter has invalid value, setting to default")
            top_n = 1

        # Send HTTP request, get response
        json_data = self.svc.get_downsampled_data(log_id,
                                                  interval=height_resol, outputformat='json',
                                                  startdepth=self.min_depth, enddepth=self.max_depth)
        if not json_data:
            LOGGER.debug("get_borehole_data() json_data= %s", repr(json_data))
            return OrderedDict()
        LOGGER.debug('json_data = %s', json_data[:100])
        meas_list = []
        depth_dict = OrderedDict()
        try:
            meas_list = json.loads(json_data.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            LOGGER.warning("Logid not known")
        else:
            # Sometimes meas_list is None
            if isinstance(meas_list, list):
                # Sort then group by depth
                sorted_meas_list = sorted(meas_list, key=lambda x: x['roundedDepth'])
                for depth, group in itertools.groupby(sorted_meas_list, lambda x: x['roundedDepth']):
                    # Filter out invalid values
                    clean_group = itertools.filterfalse(lambda x: x['classText'].upper() in ['INVALID', 'NOTAROK'],
                                                           group)

                    # Make a dict keyed on depth, value is element with largest count
                    try:
                        sorted_elem = sorted(clean_group, key=lambda x: x['classCount'], reverse=True)
                    except ValueError:
                        # Sometimes 'filtered_group' is empty
                        LOGGER.warning("No valid values at depth %s", str(depth))
                        continue
                    depth_dict[depth] = []
                    for elem in sorted_elem[:top_n]:
                        data_point = SimpleNamespace()
                        col = bgr2rgba(elem['colour'])
                        kv_dict = {'className': class_name, **elem, 'colour': col}
                        del kv_dict['roundedDepth']
                        for key, val in kv_dict.items():
                            setattr(data_point, key, val)
                        depth_dict[depth].append(data_point)
                    # If there's only one element in list, then substitute list with element
                    if top_n == 1 and len(depth_dict[depth]) == 1:
                        depth_dict[depth] = depth_dict[depth][0]

        LOGGER.debug("get_borehole_data() Returning %s", repr(depth_dict))
        return depth_dict

    def _clean_xml_parse(self, xml_str):
        ''' Filters out badly-formatted XML

        :param xml_str: XML string to parse
        :returns: XML ElementTree Element object, it will be empty if there was an error
        '''
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return ET.Element('')
        return root

    def get_datasetid_list(self, nvcl_id):
        ''' Retrieves a list of dataset ids

        :param nvcl_id: NVCL 'holeidentifier' parameter, the 'nvcl_id' from each item retrieved from 'get_feature_list()' or 'get_nvcl_id_list()'
        :returns: a list of dataset ids
        '''
        response_str = self.svc.get_dataset_collection(nvcl_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        datasetid_list = []
        for child in root.findall('./Dataset'):
            dataset_id = child.findtext('./DatasetID', default=None)
            if dataset_id:
                datasetid_list.append(dataset_id)
        return datasetid_list

    def get_dataset_list(self, nvcl_id):
        ''' Retrieves a list of dataset objects

        :param nvcl_id: NVCL 'holeidentifier' parameter, the 'nvcl_id' from each item retrieved from 'get_feature_list()' or 'get_nvcl_id_list()'
        :returns: a list of SimpleNamespace objects, attributes are: dataset_id, dataset_name, borehole_uri, tray_id, section_id, domain_id
        '''
        response_str = self.svc.get_dataset_collection(nvcl_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        dataset_list = []
        for child in root.findall('./Dataset'):
            # Compulsory
            dataset_id = child.findtext('./DatasetID', default=None)
            dataset_name = child.findtext('./DatasetName', default=None)
            if not dataset_id or not dataset_name:
                continue
            # Optional
            dataset_obj = SimpleNamespace(dataset_id=dataset_id,
                                          dataset_name=dataset_name)
            for label, key in [('borehole_uri', './boreholeURI'),
                               ('tray_id', './trayID'),
                               ('section_id', './sectionID'),
                               ('domain_id', './domainID')]:
                val = child.findtext(key, default=None)
                if val:
                    setattr(dataset_obj, label, val)
            dataset_list.append(dataset_obj)
        return dataset_list

    def get_all_imglogs(self, dataset_id):
        ''' Retrieves a list of all log objects from mosaic service

        :param dataset_id: dataset id, taken from 'get_datasetid_list()' or 'get_dataset_list()'
        :returns: a list of SimpleNamespace() objects, attributes are: log_id, log_name, sample_count. On error returns empty list
        '''
        return self._filter_mosaic_logs(dataset_id)

    def get_mosaic_imglogs(self, dataset_id):
        ''' Retrieves a list of 'Mosaic' log objects from mosaic service

        :param dataset_id: dataset id, taken from 'get_datasetid_list()' or 'get_dataset_list()'
        :return: a list of SimpleNamespace objects. Fields are: 'log_id', 'log_name', 'sample_count'. On error returns an empty list.
        '''
        return self._filter_mosaic_logs(dataset_id, 'Mosaic')

    def get_tray_thumb_imglogs(self, dataset_id):
        ''' Retrieves a list of 'Tray Thumbnail Images' log objects from mosaic service

        :param dataset_id: dataset id, taken from 'get_datasetid_list()' or 'get_dataset_list()'
        :return: a list of SimpleNamespace objects. Fields are: 'log_id', 'log_name', 'sample_count'. On error returns an empty list.
        '''
        return self._filter_mosaic_logs(dataset_id, 'Tray Thumbnail Images')

    def get_tray_imglogs(self, dataset_id):
        ''' Retrieves 'Tray Image' log objects from mosaic service

        :param dataset_id: dataset id, taken from 'get_datasetid_list()' or 'get_dataset_list()'
        :return: a list of SimpleNamespace objects. Fields are: 'log_id', 'log_name', 'sample_count'. On error returns an empty list.
        '''
        return self._filter_mosaic_logs(dataset_id, 'Tray Images')

    def get_imagery_imglogs(self, dataset_id):
        ''' Retrieves 'Imagery' log objects from mosaic service

        :param dataset_id: dataset id, taken from 'get_datasetid_list()' or 'get_dataset_list()'
        :return: a list of SimpleNamespace objects. Fields are: 'log_id', 'log_name', 'sample_count'. On error returns an empty list.
        '''

        return self._filter_mosaic_logs(dataset_id, 'Imagery')

    def _filter_mosaic_logs(self, dataset_id, target_log_name='*'):
        ''' Retrieves logs with a particular name using log collection mosaic service

        :param dataset_id: dataset id, taken from 'get_datasetid_list()' or 'get_dataset_list()'
        :param target_log_name: (optional) log name to search for. Default is '*' which retrieves all logs
        :return: a list of SimpleNamespace objects. Fields are: log_id, log_name, sample_count
        '''
        response_str = self.svc.get_log_collection(dataset_id, True)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        dataset_list = []
        for child in root.findall('./Log'):
            log_id = child.findtext('./LogID', default=None)
            log_name = child.findtext('./LogName', default=None)
            try:
                sample_count = int(child.findtext('./SampleCount', default=0))
            except ValueError:
                sample_count = 0.0
            if not log_id or not log_name:
                continue
            if target_log_name.lower() == log_name.lower() or target_log_name == '*':
                dataset_obj = SimpleNamespace(log_id=log_id,
                                              log_name=log_name,
                                              sample_count=sample_count)
                dataset_list.append(dataset_obj)
        return dataset_list

    def get_mosaic_image(self, log_id, **options):
        ''' Retrieves images of NVCL core trays

        :param log_id: obtained through calling 'get_mosaic_imglogs()' or 'get_tray_thumb_imglogs()' or 'get_tray_image_imglogs()' or 'get_imagery_imglogs()'
        :param options: optional parameters:
                 width: number of column the images are to be displayed, default value=3 (set width to 1 for full size images)
                 startsampleno: the first sample image to be displayed, default value=0
                 endsampleno: the last sample image to be displayed, default value=99999

        :returns: NVCL core tray images
        '''
        return self.svc.get_mosaic(log_id, **options)

    def get_tray_thumb_html(self, dataset_id, log_id, **options):
        ''' Gets core tray thumbnail images as HTML

        :param dataset_id: obtained through calling 'get_datasetid_list()'
        :param log_id: obtained through calling 'get_tray_thumb_imglogs()'
        :param width: specify the number of column the images are to be displayed, default value=3
        :param startsampleno: the first sample image to be displayed, default value=0
        :param endsampleno: the last sample image to be displayed, default value=99999

        :returns: thumbnail image in HTML format
        '''
        return self.svc.get_mosaic_tray_thumbnail(dataset_id, log_id, **options)

    def get_tray_thumb_jpg(self, log_id, sample_no='0'):
        ''' Gets core tray thumbnail images as JPEG

        :param log_id: obtained through calling 'get_tray_thumb_imglogs()'
        :param sample_no: sample number, string e.g. '0','1','2'...  optional, default is '0'

        :returns: thumbnail image in PNG format
        '''
        return self.svc.get_display_tray_thumb(log_id, sample_no)

    def get_tray_depths(self, log_id):
        ''' Gets tray depths

        :param log_id: obtained through calling 'get_tray_thumb_imglogs()' or 'get_tray_imglogs()'

        :returns: a list of SimpleNamespace objects, with attributes: 'sample_no', 'start_value' and 'end_value'
        '''
        response_str = self.svc.get_image_tray_depth(log_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        image_tray_list = []
        for child in root.findall('./ImageTray'):
            sample_no = child.findtext('./SampleNo', default=None)
            start_value = child.findtext('./StartValue', default=None)
            end_value = child.findtext('./EndValue', default=None)
            if not sample_no or not start_value or not end_value:
                continue
            image_tray_obj = SimpleNamespace(sample_no=sample_no,
                                             start_value=start_value,
                                             end_value=end_value)
            image_tray_list.append(image_tray_obj)
        return image_tray_list

    def get_scalar_logs(self, dataset_id):
        ''' Retrieves a list of log objects for scalar plot service

        :param dataset_id: dataset_id, taken from 'get_datasetid_list()' or 'get_dataset_list()'

        :returns: a list of SimpleNamespace() objects, attributes are: log_id, log_name, is_public, log_type, algorithm_id. On error returns empty list
        '''
        response_str = self.svc.get_log_collection(dataset_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        log_list = []
        for child in root.findall('./Log'):
            log_id = child.findtext('./LogID', default=None)
            log_name = child.findtext('./logName', default=None)
            is_public = child.findtext('./ispublic', default=None)
            if ENFORCE_IS_PUBLIC and is_public and is_public.upper() == 'FALSE':
                continue
            log_type = child.findtext('./logType', default=None)
            algorithm_id = child.findtext('./algorithmoutID', default=None)
            # Only types 1,2,5,6 can be used
            if log_id and log_name and log_type in ['1', '2', '5', '6'] and algorithm_id:
                log = SimpleNamespace(log_id=log_id,
                                      log_name=log_name,
                                      is_public=is_public,
                                      log_type=log_type,
                                      algorithm_id=algorithm_id)
                log_list.append(log)
        return log_list

    def get_scalar_data(self, log_id_list):
        ''' Downloads scalar data in CSV format

        :param log_id_list: a list of log ids obtained through calling 'get_scalar_logs()'

        :returns: scalar data in CSV format
        '''
        return self.svc.download_scalar(log_id_list)

    def get_sampled_scalar_data(self, log_id, **options):
        ''' Returns data in downsampled format, to a certain height resolution

        :param log_id: obtained through calling 'get_scalar_logs()'
        :param outputformat: (optional) string 'csv' or 'json'
        :param startdepth: (optional) start of depth range, in metres from borehole
            collar
        :param enddepth: (optional) end of depth range, in metres from borehole
            collar
        :param interval: (optional) resolution to bin or average over
        '''
        return self.svc.get_downsampled_data(log_id, **options)

    def plot_scalar_png(self, log_id, **options):
        ''' Draws a plot as an image in PNG format.

        :param log_id: obtained through calling 'get_scalar_logs()'
        :param startdepth: (optional) the start depth of a borehole collar,
             default value=0
        :param enddepth: (optional) the end depth of a borehole collar,
             default value=99999
        :param samplinginterval: (optional) the interval of the sampling,
             default value=1
        :param width: (optional) the width of the image in pixel, default value=300
        :param height: (optional) the height of the image in pixel,
             default value=600
        :param graphtype: (optional) an integer range from 1 to 3,
             1=Stacked Bar Chart, 2=Scattered Chart, 3=Line Chart, default value=1
        :param legend: (optional) value=1 or 0, 1 - indicates to show the legend,
             0 to hide it, optional, default to 1

        :returns: a 2d plot as a PNG image
        '''
        return self.svc.get_plot_scalar(log_id, **options)

    def plot_scalars_html(self, log_id_list, **options):
        ''' Draws multiple plots, returned in HTML format

        :param log_id_list: a list of up to 6 log ids, obtained through calling
               'get_scalar_logs()'
        :param startdepth: (optional) the start depth of a borehole collar,
             default value=0
        :param enddepth: (optional) the end depth of a borehole collar,
             default value=99999
        :param samplinginterval: (optional) the interval of the sampling,
             default value=1
        :param width: (optional) the width of the image in pixel,
             default value=300
        :param height: (optional) the height of the image in pixel,
             default value=600
        :param graphtype: (optional) an integer range from 1 to 3,
             1=Stacked Bar Chart, 2=Scattered Chart, 3=Line Chart, default value=1
        :param legend: (optional) value=yes or no, if yes - indicate to show the
             legend, default to yes

        :returns: one or more 2d plots as HTML
        '''
        # NB: Service only plots the first 6 log ids
        return self.svc.get_plot_multi_scalar(log_id_list[:6], **options)

    def get_algorithms(self):
        ''' Gets a dict of algorithm output ids and their versions

        :returns: a dict of { 'algorithmOutputId1': 'version1', 'algorithmOutputId2': 'version2', ... }
        '''
        alg_str = self.svc.get_algorithms()
        try:
            xml_tree = ET.fromstring(alg_str)
            algver_dict = {}
            for alg in xml_tree.findall('algorithms/outputs/versions'):
                alg_id = alg.find('algorithmoutputID')
                ver = alg.find('version')
                if alg_id is not None and ver is not None:
                    algver_dict[alg_id.text] = ver.text
        except ET.ParseError as pe_exc:
            LOGGER.debug(f"get_algorithms() failed to parse response: {pe_exc}")
            return {}
        return algver_dict

    def get_imagelog_data(self, nvcl_id):
        ''' Retrieves a set of image log data for a particular borehole

        :param nvcl_id: NVCL 'holeidentifier' parameter,
                        the 'nvcl_id' from each item retrieved from 'get_feature_list()' or 'get_nvcl_id_list()'

        :returns: a list of SimpleNamespace() objects with attributes:
                  log_id, log_type, log_name
        '''
        response_str = self.svc.get_dataset_collection(nvcl_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        logid_list = []
        for child in root.findall('./*/Logs/Log'):
            is_public = child.findtext('./ispublic', default='false')
            log_name = child.findtext('./logName', default='')
            log_type = child.findtext('./logType', default='')
            log_id = child.findtext('./LogID', default='')
            alg_id = child.findtext('./algorithmoutID', default='')
            if (is_public == 'true' or not ENFORCE_IS_PUBLIC) and log_name != '' and log_type != '' and log_id != '':
                logid_list.append(SimpleNamespace(log_id=log_id, log_type=log_type, log_name=log_name,
                                                  algorithmout_id=alg_id))
        return logid_list

    def get_spectrallog_data(self, nvcl_id):
        ''' Retrieves a set of spectral log data for a particular borehole

        :param nvcl_id: NVCL 'holeidentifier' parameter,
                        the 'nvcl_id' from each item retrieved from 'get_feature_list()' or 'get_nvcl_id_list()'

        :returns: a list of SimpleNamespace() objects with attributes:
                  log_id, log_name, wavelength_units, sample_count, script,
                  wavelengths
        '''
        response_str = self.svc.get_dataset_collection(nvcl_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        logid_list = []
        for child in root.findall('./*/SpectralLogs/SpectralLog'):
            log_id = child.findtext('./logID', default='')
            log_name = child.findtext('./logName', default='')
            wavelength_units = child.findtext('./wavelengthUnits', default='')
            try:
                sample_count = int(child.findtext('./sampleCount', default=0))
            except ValueError:
                sample_count = 0
            script_raw = child.findtext('./script', default='')
            script_str = script_raw.replace('; ', ';')
            script_str_list = script_str.split(';')
            script_dict = {}
            for assgn in script_str_list:
                var, eq, val = assgn.partition('=')
                if var and eq == '=':
                    script_dict[var] = val
            wavelengths = child.findtext('./wavelengths', default='')
            try:
                wv_list = [float(wv_str) for wv_str in wavelengths.split(',')]
            except ValueError:
                wv_list = []
            logid_list.append(SimpleNamespace(log_id=log_id, log_name=log_name, wavelength_units=wavelength_units,
                                              sample_count=sample_count, script_raw=script_raw, script=script_dict,
                                              wavelengths=wv_list))
        return logid_list

    def get_spectrallog_datasets(self, log_id, **options):
        ''' Retrieves spectral log datasets as a binary string

        :param log_id: obtained through calling 'get_spectrallog_data()'
        :param start_sample_no: retrieve sample numbers starting from this string e.g. '0'
        :param end_sample_no: retrieve sample numbers ending with this string e.g. '2'

        :returns: a binary text string
        '''
        in_opts = {}
        if 'start_sample_no' in options:
            in_opts.update({ 'startsampleno': options['start_sample_no']})
        if 'end_sample_no' in options:
            in_opts.update({ 'endsampleno': options['end_sample_no']})
        return self.svc.get_spectral_data(log_id, **in_opts)

    def get_profilometer_data(self, nvcl_id):
        ''' Retrieves a set of profilometer logs for a particular borehole

        :param nvcl_id: NVCL 'holeidentifier' parameter,
                        the 'nvcl_id' from each item retrieved from 'get_feature_list()' or 'get_nvcl_id_list()'

        :returns: a list of SimpleNamespace() objects with attributes:
                  log_id, log_name, sample_count, floats_per_sample,
                  min_val, max_val
        '''
        response_str = self.svc.get_dataset_collection(nvcl_id)
        if not response_str:
            return []
        root = self._clean_xml_parse(response_str)
        logid_list = []
        for child in root.findall('./*/ProfilometerLogs/ProfLog'):
            log_id = child.findtext('./logID', default='')
            log_name = child.findtext('./logName', default='')
            try:
                sample_count = int(child.findtext('./sampleCount', default=0))
            except ValueError:
                sample_count = 0.0
            try:
                floats_per_sample = float(child.findtext('./floatsPerSample', default=0.0))
            except ValueError:
                floats_per_sample = 0.0
            try:
                min_val = float(child.findtext('./minVal', default=0.0))
            except ValueError:
                min_val = 0.0
            try:
                max_val = float(child.findtext('./maxVal', default=0.0))
            except ValueError:
                max_val = 0.0
            logid_list.append(SimpleNamespace(log_id=log_id, log_name=log_name, sample_count=sample_count, floats_per_sample=floats_per_sample, min_val=min_val, max_val=max_val))
        return logid_list

    def get_boreholes_list(self):
        ''' Returns a list of dictionary objects, extracted from WFS requests of boreholes. Fields are mostly taken from GeoSciML v4.1 Borehole View:

            'nvcl_id', 'identifier', 'name', 'description', 'purpose', 'status', 'drillingMethod', 'operator', 'driller', 'drillStartDate', 'drillEndDate', 'startPoint', 'inclinationType', 'href', 'boreholeMaterialCustodian', 'boreholeLength_m', 'elevation_m', 'elevation_srs', 'positionalAccuracy', 'source', 'x', 'y, 'z', 'parentBorehole_uri', 'metadata_uri', 'genericSymbolizer'

            NB:
                (1) Depending on the WFS, not all fields will have values
                (2) 'href' corresponds to 'gsmlp:identifier'
                (3) 'x', 'y', 'z' are x-coordinate, y-coordinate and elevation
                (4) 'nvcl_id' is the GML 'id', used as an id in the NVCL services

            :returns: a list of dictionaries whose fields correspond to a response from a WFS request of GeoSciML v4.1 BoreholeView
        '''
        return self.borehole_list

    def get_feature_list(self):
        ''' Returns a list of SimpleNamespace objects, extracted from WFS requests of boreholes. Fields are mostly taken from GeoSciML v4.1 Borehole View:

            'nvcl_id', 'identifier', 'name', 'description', 'purpose', 'status', 'drillingMethod', 'operator', 'driller', 'drillStartDate', 'drillEndDate', 'startPoint', 'inclinationType', 'href', 'boreholeMaterialCustodian', 'boreholeLength_m', 'elevation_m', 'elevation_srs', 'positionalAccuracy', 'source', 'x', 'y, 'z', 'parentBorehole_uri', 'metadata_uri', 'genericSymbolizer'

            NB:
                (1) Depending on the WFS, not all fields will have values
                (2) 'href' corresponds to 'gsmlp:identifier'
                (3) 'x', 'y', 'z' are x-coordinate, y-coordinate and elevation
                (4) 'nvcl_id' is the GML 'id', used as an id in the NVCL services

            :returns: a list of SimpleNamespace objects whose fields correspond to a response from a WFS request of GeoSciML v4.1 BoreholeView
        '''
        return [ SimpleNamespace(**bh) for bh in self.borehole_list]

    def get_nvcl_id_list(self):
        '''
        Returns a list of NVCL ids, can be used as input to other 'nvcl_kit' API
        calls e.g. get_spectrallog_data()

        :returns: a list of NVCL id strings
        '''
        return [bh['nvcl_id'] for bh in self.borehole_list]

    def _clean_wfs_resp(self, getfeat_params):
        '''
        Fetches WFS response from owslib and make sure it returns a byte string

        :param getfeat_params: dict of parameters for WFS GetFeature request

        :returns: byte string response
        '''
        
        LOGGER.debug("_clean_wfs_resp(params=%s)", str(getfeat_params))
        response = self.wfs.getfeature(**getfeat_params).read()
        LOGGER.debug("_clean_wfs_resp(): response=%s", repr(response))
        if not type(response) in [bytes, str]:
            response_str = b""
        elif type(response) == bytes:
            response_str = response
        else:
            response_str = response.encode('utf-8', 'ignore')
        return response_str

    def _wfs_getfeature(self):
        response_str = b''
        bhv_list = []
        # Don't use local filtering, can be both WFS v1.1.0 or v2.0.0
        if not self.param_obj.USE_LOCAL_FILTERING:
            # FIXME: Can't filter for BBOX and nvclCollection==true at the same time
            # [owslib's BBox uses 'ows:BoundingBox', not supported in WFS]
            # so is best to do the BBOX manually
            filter_prop = PropertyIsLike(propertyname='gsmlp:nvclCollection', literal='true', matchCase=False)
            # filter_2 = BBox([self.param_obj.BBOX['west'], self.param_obj.BBOX['south'], self.param_obj.BBOX['east'],
            #              self.param_obj.BBOX['north']], crs=self.param_obj.BOREHOLE_CRS)
            # filter_3 = And([filter_, filter_2])
            filterxml = etree.tostring(filter_prop.toXML()).decode("utf-8")
            try:
                getfeat_params = {'typename': 'gsmlp:BoreholeView', 'filter': filterxml}
                if self.param_obj.WFS_VERSION != '2.0.0':
                    getfeat_params['srsname'] = self.param_obj.BOREHOLE_CRS
                response_str = self._clean_wfs_resp(getfeat_params)
            except (RequestException, HTTPException, ServiceException, OSError) as exc:
                LOGGER.warning("WFS GetFeature failed, filter=%s: %s", filterxml, str(exc))
                return bhv_list
            root = self._clean_xml_parse(response_str)
            return root.findall('./*/gsmlp:BoreholeView', NS)

        # Using local filtering, only supported in WFS v2.0.0
        elif self.param_obj.WFS_VERSION == "2.0.0":
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
                    LOGGER.debug('_wfs_getfeature(): getfeat_params = %s', repr(getfeat_params))
                    resp_s = self._clean_wfs_resp(getfeat_params)
                    LOGGER.debug('_wfs_getfeature(): resp_s = %s', resp_s)
                except (RequestException, HTTPException, ServiceException, OSError) as exc:
                    LOGGER.warning(f"WFS GetFeature failed: {exc}")
                    return bhv_list
                record_cnt += RECORD_INC
                root = self._clean_xml_parse(resp_s)
                bhv_list += [x for x in root.findall('./*/gsmlp:BoreholeView', NS)]
                num_ret = root.attrib.get('numberReturned', '0')
                LOGGER.debug('_wfs_getfeature(): num_ret = %s',  num_ret)
                LOGGER.debug('record_cnt = %d', record_cnt)
                done = num_ret == '0'

            return bhv_list
        else:
            LOGGER.error("Cannot have USE_LOCAL_FILTERING and WFS_VERSION < 2.0.0")
            return []

    def filter_feat_list(self, nvcl_ids_only=False, **kwargs):
        ''' Returns a list of borehole features given a filter parameter
            Filter parameters can be one of those returned by 'get_feature_list' e.g.

            new_list = filter_feat_list(name='ML006')

        :param kwargs: keyword arguments key is name searched for, val is a list of possible values or a single value
        :param nvcl_ids_only: if True will return a list of nvcl_id

        :returns: a list of borehole features or empty list if unsuccessful
        '''
        for key, val in kwargs.items():
            val_list = val
            if not isinstance(val,list):
                val_list = [val]
            bh_list = [ bh for bh in self.borehole_list if key in bh and bh[key] in val]
                
            if not nvcl_ids_only:
                return [ SimpleNamespace(**bh) for bh in bh_list ]
            else:
                return [ bh['nvcl_id'] for bh in bh_list ]

        return []


    def _fetch_borehole_list(self, names=[], ids=[]):
        ''' Returns a list of WFS borehole data within bounding box, but only NVCL boreholes
            [ { 'nvcl_id': XXX, 'x': XXX, 'y': XXX, 'href': XXX, ... }, { ... } ]
            See description of 'get_boreholes_list()' for more info

        :returns: True if operation succeeded
        '''
        LOGGER.debug("_fetch_boreholes_list()")
        bhv_list = self._wfs_getfeature()
        if len(bhv_list) == 0:
            LOGGER.debug('_fetch_boreholes_list(): No response')
            return False
        LOGGER.debug('len(bhv_list) = %d', len(bhv_list))
        LOGGER.debug('bhv_list = %s', repr(bhv_list))
        borehole_cnt = 0
        record_cnt = 0

        for i in range(len(bhv_list)):
            LOGGER.debug('i = %d', i)
            child = bhv_list[i]
            LOGGER.debug('len(bhv_list) = %d', len(bhv_list))
            LOGGER.debug('child = %s',  ET.tostring(child))
            # WFS v2.0.0 uses gml32
            if self.param_obj.WFS_VERSION == '2.0.0':
                id_str = '{' + NS['gml32'] + '}id'
            else:
                id_str = '{' + NS['gml'] + '}id'
            nvcl_id = child.attrib.get(id_str, '').split('.')[-1:][0]

            # Some services don't use a namepace for their id
            if nvcl_id == '':
                nvcl_id = child.attrib.get('id', '').split('.')[-1:][0]

            is_nvcl = child.findtext('./gsmlp:nvclCollection', default="?????", namespaces=NS)
            LOGGER.debug("is_nvcl = %s", is_nvcl)
            LOGGER.debug("nvcl_id = %s", nvcl_id)
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
                LOGGER.debug('x_y = %s', repr(x_y))

                try:
                    # See https://docs.geoserver.org/latest/en/user/services/wfs/axis_order.html#wfs-basics-axis
                    if self.param_obj.BOREHOLE_CRS != 'EPSG:4326' or \
                           reverse_coords:
                        # latitude/longitude or y,x order
                        borehole_dict['y'] = float(x_y[0])  # lat
                        borehole_dict['x'] = float(x_y[1])  # lon
                    else:
                        # longitude/latitude or x,y order
                        borehole_dict['x'] = float(x_y[0])  # lon
                        borehole_dict['y'] = float(x_y[1])  # lat
                except (OSError, ValueError) as os_exc:
                    LOGGER.warning("Cannot parse collar coordinates %s", str(os_exc))
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

                LOGGER.debug(f"borehole_dict = {repr(borehole_dict)}")
                LOGGER.debug(f"BBOX={self.param_obj.BBOX}")
                LOGGER.debug('%s < %s, %s > %s',
                             self.param_obj.BBOX['west'], borehole_dict['x'],
                             self.param_obj.BBOX['east'], borehole_dict['x'])
                LOGGER.debug('%s > %s, %s < %s',
                             self.param_obj.BBOX['north'], borehole_dict['y'],
                             self.param_obj.BBOX['south'], borehole_dict['y'])

                # If POLYGON is set, only accept if within linear ring
                if hasattr(self.param_obj, 'POLYGON'):
                    point = Point(borehole_dict['x'], borehole_dict['y'])
                    if point.within(self.param_obj.POLYGON):
                        borehole_cnt += 1
                        self.borehole_list.append(borehole_dict)
                        LOGGER.debug("borehole_cnt = %d", borehole_cnt)

                # Else only accept if within bounding box
                elif (self.param_obj.BBOX['west'] < borehole_dict['x'] and
                      self.param_obj.BBOX['east'] > borehole_dict['x'] and
                      self.param_obj.BBOX['north'] > borehole_dict['y'] and
                      self.param_obj.BBOX['south'] < borehole_dict['y']):
                    borehole_cnt += 1
                    self.borehole_list.append(borehole_dict)
                    LOGGER.debug("borehole_cnt = %d", borehole_cnt)

                if self.param_obj.MAX_BOREHOLES > 0 and borehole_cnt >= self.param_obj.MAX_BOREHOLES:
                    break
            record_cnt += 1
            LOGGER.debug('record_cnt = %d', record_cnt)
        LOGGER.debug('_fetch_boreholes_list() returns True')
        return True
