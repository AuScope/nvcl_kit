"""
This forms the interface between the 'reader' class and the low-level web APIs.

"""
import hashlib
import os
import time
import urllib
import urllib.parse
import urllib.request
from http.client import HTTPException
from socket import timeout
import sys
import logging

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


class _ServiceInterface:
    ''' Call the web APIs for NVCL services

        NB: 'ServiceInterface' should only be called from within the 'reader' class.
    '''

    def __init__(self, nvcl_url, timeout, cache_path = None):
        '''
        :param nvcl_url: URL of the NVCL service
        :param timeout: initial timeout value for connection to NVCL service, doubles at each attempt, 5 attempts in total (seconds)
        :param cache_path: optional folder path for cache files
        '''
        self.NVCL_URL = nvcl_url
        self.CACHE_PATH = cache_path
        self.TIMEOUT = timeout

    def get_algorithms(self):
        ''' Retrieves a list of algorithms and their output ids
        '''
        url = self.NVCL_URL + '/getAlgorithms.html'
        return self._get_response_str(url)

    def get_dataset_collection(self, nvcl_id, **options):
        ''' Retrieves a dataset for a particular borehole

        :param nvcl_id: NVCL 'holeidentifier' parameter, the 'nvcl_id' from each dict item retrieved from
                  'get_boreholes_list()' or 'get_nvcl_id_list()'
        :param options: optional parameters:

            * headersOnly: only get dataset headers, this is much faster and can be used in combination with holeidentifier=all to get a list of all datasets efficiently, example value=yes
            * outputformat: change output format from xml, example value=json

        :returns: the response as a byte string or an empty string upon error
        '''
        url = self.NVCL_URL + '/getDatasetCollection.html'
        params = {'holeidentifier': nvcl_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_mosaic(self, log_id, **options):
        ''' Retrieves images of NVCL core trays

        :param log_id: obtained through calling the getLogCollection service with URL parameter mosaicsvc=yes
        :param options: optional parameters:

             * width: number of column the images are to be displayed, default value=3
             * startsampleno: the first sample image to be displayed, default value=0
             * endsampleno: the last sample image to be displayed, default value=99999
        '''
        url = self.NVCL_URL + '/mosaic.html'
        params = {'logid': log_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_mosaic_tray_thumbnail(self, dataset_id, log_id, **options):
        ''' Retrieves thumbnail images of NVCL core trays

        :param dataset_id: obtained through calling the getDatasetCollection service
        :param logid: obtained through calling the getLogCollection service by specifying URL Parameter mosaicsvc=yes, with LogName equal Tray Thumbnail Images
        :param options: optional parameters:

              * width: specify the number of column the images are to be displayed, default value=3
              * startsampleno: the first sample image to be displayed, default value=0
              * endsampleno: the last sample image to be displayed, default value=99999
        '''
        url = self.NVCL_URL + '/mosaictraythumbnail.html'
        params = {'datasetid': dataset_id, 'logid': log_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_display_tray_thumb(self, log_id, sample_no):
        ''' Gets thumbnail images of NVCL core trays

        :param log_id: obtained through calling the getLogCollection service by specifying URL Parameter mosaicsvc=yes
        :param sample_no: sample number of the image to retrieve from database
        '''
        url = self.NVCL_URL + '/Display_Tray_Thumb.html'
        params = {'logid': log_id, 'sampleno': sample_no}
        return self._get_response_str(url, params)

    def get_image_tray_depth(self, log_id):
        ''' Generates a list of image tray collection with start and end depth values for each image tray.

        :param logid: obtained through calling the getLogCollection service with mosaicsvc set to yes, select the LogId with LogName equal Tray Thumbnail Images or Tray Images
        '''
        url = self.NVCL_URL + '/getImageTrayDepth.html'
        params = {'logid': log_id}
        return self._get_response_str(url, params)

    def get_plot_scalar(self, log_id, **options):
        ''' Uses JFeeChart Java chart library to draw a plot of the product and return the plot as an image in PNG format.

        :param log_id: obtained through calling the getLogCollection service with mosaicsvc URL parameter set to 'no'
        :param options: a dict of options:

               * startdepth: the start depth of a borehole collar, defaultvalue = 0
               * enddepth: the end depth of a borehole collar, default value=99999
               * samplinginterval: the interval of the sampling, default value=1
               * width: the width of the image in pixel, default value=300
               * height: the height of the image in pixel, default value=600
               * graphtype: an integer range from 1 to 3, 1=Stacked Bar Chart, 2=Scattered Chart, 3=Line Chart, default value=1
               * legend: value= 1 or 0, 1 - indicates to show the legend, 0 to hide it, optional, default to 1
        '''
        url = self.NVCL_URL + '/plotscalar.html'
        params = {'logid': log_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_plot_multi_scalar(self, log_id_list, **options):
        ''' Same as 'get_plot_scalar' above, except that it returns HTML

        :param log_id_list: obtained through calling the getLogCollection
             service, with mosaicsvc URL parameter set to 'no' and up to 6
             logid parameters are allowed
        :param options: optional parameters:

               * startdepth: the start depth of a borehole collar, default value=0
               * enddepth: the end depth of a borehole collar, default value=99999
               * samplinginterval: the interval of the sampling, default value=1
               * width: the width of the image in pixel, default value=300
               * height: the height of the image in pixel, default value=600
               * graphtype: an integer range from 1 to 3, 1=Stacked Bar Chart, 2=Scattered Chart, 3=Line Chart, default value=1
               * legend: value=yes or no, if yes - indicate to show the legend, default to yes
        '''
        url = self.NVCL_URL + '/plotmultiscalars.html'
        if not log_id_list:
            return ""
        params = self._make_multi_logids(log_id_list, options)
        return self._get_response_str(url, params)

    def download_scalar(self, log_id_list):
        ''' This service enables download of the raw scalar values in csv format

        :param log_id: obtained through calling the getLogCollection service, with mosaicsvc URL parameter set to 'no' and multiple logid parameters are allowed
        :return: scalars in CSV format
        '''
        url = self.NVCL_URL + '/downloadscalars.html'
        params = self._make_multi_logids(log_id_list)
        return self._get_response_str(url, params)

    def download_tsg(self, email, dataset_id, **options):
        ''' When triggered, the TSG download Service will prepare TSG files from NVCL database datasets and make them available for download.

        :param email: user's email address to identify the user
        :param dataset_id: GUID dataset identifier of the dataset to be prepared (list of datasetid can be obtained through calling the NVCL Data Services getDatasetCollection service)
        :param options: optional parameters:

            * linescan: Prepare linescan imagery with this dataset. Setting this
              to 'no' will reduce the size of the download significantly but
              users will not be able to see the highest resolution images.  Default value=yes
            * forcerecreate: Force the service to delete the cached version of
              this dataset and recreate it. Use this if there is a problem with
              the dataset or cached version is stale. Default value=no
        '''
        url = self.NVCL_URL + '/downloadtsg.html'
        params = {'email': email, 'datasetid': dataset_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_download_tsg_status(self, email):
        ''' This service displays the status of past TSG file download requests for users. This service takes a single parameter which is the email address of the user.

        :param email: user's email address to identify the user
        '''
        url = self.NVCL_URL + '/checktsgstatus.html'
        return self._get_response_str(url, {'email': email})

    def download_wfs(self, email, borehole_id, options):
        ''' The WFS Download Service will prepare xml datasets from NVCL GeoServer instances and make them available for download.

        :param email: user's email address to identify the user
        :param borehole_id: gml feature identifier of the dataset to be prepared
        :param options: dictionary of optional parameters:

            * typename: the type name of the gml feature to prepare; default value
              is 'sa:SamplingFeatureCollection'.
            * forcerecreate: Force the Service to delete the cached version of
              this dataset and recreate it. Use this if there is a problem with
              the dataset or cached version is stale; default value=no
        '''
        url = self.NVCL_URL + '/downloadwfs.html'
        params = {'email': email, 'boreholeid': borehole_id}
        params.update(options)
        return self._get_response_str(url, params)

    def download_wfs_status(self, email):
        ''' This service displays the status of past WFS file download requests.

        :param email: user's email address to identify the user
        '''
        url = self.NVCL_URL + '/checkwfsstatus.html'
        return self._get_response_str(url, {'email': email})

    def get_log_collection(self, dataset_id, use_mosaic=False):
        ''' Retrieves log details for a particular borehole's dataset

        :param dataset_id: dataset id parameter,
                        the 'dataset_id' from each dict item retrieved from 'get_datasetid_list()' or 'get_dataset_data()'
        :param mosaic_svc: NVCL 'mosaic_svc' parameter, if true retrieves mosaic
                           data, else scalar; boolean
        :returns: the response as a byte string or an empty string upon error
        '''
        url = self.NVCL_URL + '/getLogCollection.html'
        mosaic_svc = 'no'
        if use_mosaic:
            mosaic_svc = 'yes'
        params = {'datasetid': dataset_id, 'mosaicsvc': mosaic_svc}
        return self._get_response_str(url, params)

    def get_spectral_data(self, spec_log_id, **options):
        ''' Fetches binary spectral data

        :param spec_log_id: spectral log id
        :param optional parameters:

            * startsampleno: starting sample number
            * endsampleno: ending sample number
        '''
        url = self.NVCL_URL + '/getspectraldata.html'
        params = {'speclogid': spec_log_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_downsampled_data(self, log_id, **options):
        ''' Returns data in downsampled format, to a certain height resolution

        :param log_id: obtained through calling the getLogCollection service with URL parameter mosaicsvc=yes
        :param options: dictionary of optional parameters:

            * outputformat: string 'csv' or 'json'
            * startdepth: start of depth range, in metres from borehole collar
            * enddepth: end of depth range, in metres from borehole collar
            * interval: size of interval to bin or average over
        '''
        url = self.NVCL_URL + '/getDownsampledData.html'
        params = {'logid': log_id}
        params.update(options)
        return self._get_response_str(url, params)

    def get_prof_data(self, proflog_id, **options):
        ''' Retrieves profilometer data in the form of binary chunks or json.

        :param proflog_id: profilometer log id obtained through the get_dataset_collection service
        :param options: dictionary of optional parameters:

            * startsampleno: the sample number of the first profilometer data point to be returned, default = '0'
            * endsampleno: the sample number of the last profilometer data point to be returned, default = '999999'
            * outputformat: string 'binary' or 'json', default = 'binary'
        '''
        url = self.NVCL_URL + '/getprofdata.html'
        params = {'proflogid': proflog_id}
        params.update(options)
        return self._get_response_str(url, params)

    def _get_response_str(self, url, params=None):
        ''' Performs a GET request with URL and parameters and returns the response as a string

        :param url: URL of request, string
        :param params: parameters, in dictionary form
        :return: response, string; returns an empty string upon error
        '''
        enc_params = None
        if params is not None:
            enc_params = urllib.parse.urlencode(params).encode('ascii')
        req = urllib.request.Request(url, data=enc_params)
        LOGGER.debug(f"Sending: {url}, {enc_params}")
        response_str = b''
        fileCachePath = None
        if (self.CACHE_PATH is not None):
            fileCachePath = self.CACHE_PATH + urllib.parse.quote(f'{url}?{enc_params.decode("utf-8")}', '')+'.txt'
            if len(fileCachePath) > 256:
                param = hashlib.sha1(enc_params).hexdigest()
                fileCachePath = self.CACHE_PATH + urllib.parse.quote(f'{url}?{param}', '')+'.txt'
            if (os.path.exists(fileCachePath)):
                with open(fileCachePath, 'rb') as cacheFile:
                    response_str = cacheFile.read()
                    LOGGER.debug(f'read cache:{fileCachePath}')
                    return response_str
        for cc in range(5):
            try:
                # TODO: Upgrade to requests & urllib3 timeout and error management
                with urllib.request.urlopen(req, timeout=self.TIMEOUT*2**cc) as response:
                    response_str = response.read()
                    break
            except HTTPException as he_exc:
                LOGGER.warning(f"HTTP Error with {url}: {he_exc}")
                return ""
            except OSError as os_exc:
                # Catch and retry timeouts
                if isinstance(os_exc, timeout):
                    LOGGER.debug(f"Timeout with {url} retry: #{cc+1}")
                    if cc < 5:
                        time.sleep(1)
                        continue
                LOGGER.warning(f"OS Error with {url}: {os_exc}")
                return ""
        LOGGER.debug(f"Response[:100]: {response_str[:100]}")

        if (self.CACHE_PATH is not None and not os.path.exists(fileCachePath)):
            with open(fileCachePath, 'wb') as cacheFile:
                cacheFile.write(response_str)
                cacheFile.close()
                LOGGER.debug(f'write cache:{fileCachePath}')
        return response_str

    def _make_multi_logids(self, log_id_list, options={}):
        ''' Converts a list of log ids to a logids for a HTTP GET request
              e.g. ['XX','YY','ZZ'] converts to 'logid=XX&logid=YY&logid=ZZ'

        :param log_id_list: log id list to be converted
        :returns: logid GET request string
        '''
        params = [('logid', log_id) for log_id in log_id_list]
        params += list(options.items())
        return params
