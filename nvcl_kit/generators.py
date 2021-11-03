'''
A collection of generator functions to make it easy to create scalar datasets, core images and plots
'''

from types import SimpleNamespace
from nvcl_kit.constants import Scalar

def gen_scalar_by_depth(reader, *, nvcl_id_list=None, resolution=20.0, scalar_class=Scalar.ANY, log_type=None, top_n=5):
    ''' Returns scalar borehole data ordered by depth given filter parameters

    :param nvcl_id_list: optional list of nvcl ids
    :param resolution: optional nvcl_kit.constants.Scalar class object, default Scalar.ANY
    :param log_type: optional log type e.g. '1' or '2'
    :param top_n: optional, only retrieve the first n scalara at each depth, default  value is 5
    :return: yields a tuple of (nvcl_id, image log object, scalar data object)
    '''
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list() 
        if not nvcl_id_list:
            raise StopIteration()
    
    for n_id in nvcl_id_list:
        imagelog_data_list = reader.get_imagelog_data(n_id)
        if imagelog_data_list:
            for ild in imagelog_data_list:
                if (log_type is None or ild.log_type == log_type) and \
                   (ild.log_name == scalar_class or scalar_class == Scalar.ANY):
                    scalar_data = reader.get_borehole_data(ild.log_id, resolution, ild.log_name, top_n=top_n)
                    yield n_id, ild, scalar_data


def gen_downhole_scalar_plots(reader, *, nvcl_id_list=None):
    ''' Returns scalar downhole plots

    :param nvcl_id_list: optional list of nvcl ids
    :return: yields a tuple of (nvcl id, dataset id, scalar data object, PNG image byte array)
    '''
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list() 
        if not nvcl_id_list:
            raise StopIteration()

    for n_id in nvcl_id_list:
        datasetid_list = reader.get_datasetid_list(n_id)
        if datasetid_list:
            for dsid in datasetid_list:
                scalar_log_list = reader.get_scalar_logs(dsid)
                for scalar_log in scalar_log_list:
                    png = reader.plot_scalar_png(scalar_log.log_id)
                    yield n_id, dsid, scalar_log, png


def gen_tray_thumb_imgs(reader, *, nvcl_id_list=None):
    ''' Returns core tray images

    :param nvcl_id_list: optional list of nvcl ids
    :return: yields a tuple of (nvcl id, dataset id, image log object, tray depth list, JPEG image byte array)
    '''
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list() 
        if not nvcl_id_list:
            raise StopIteration()

    for n_id in nvcl_id_list:
        datasetid_list = reader.get_datasetid_list(n_id)
        if datasetid_list:
            for dsid in datasetid_list:
                ilog_list = reader.get_tray_thumb_imglogs(dsid)
                for ilog in ilog_list:
                    image_data = reader.get_tray_thumb_jpg(ilog.log_id)
                    depth_list = reader.get_tray_depths(ilog.log_id)
                    yield n_id, dsid, ilog, depth_list, image_data

    
def gen_core_images(reader, *, nvcl_id_list=None, startsampleno=0, endsampleno=10, max_magnify=False): 
    ''' Returns core images given filter parameters

    :param nvcl_id_list: optional list of nvcl ids
    :param startsampleno: optional start sample number, default is 0
    :param endsampleno: optional end sample number, default is 10
    :param max_magnify: optional, when True it will return close up images of core, default is False
    :return: yields a tuple of (nvcl id, dataset id, image log object, tray depth list, image html)
    '''
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list() 
        if not nvcl_id_list:
            raise StopIteration()

    width=0
    if max_magnify:
        width=1 
    for n_id in nvcl_id_list:
        datasetid_list = reader.get_datasetid_list(n_id)
        if datasetid_list:
            for ds_id in datasetid_list:
                img_log_list = reader.get_imagery_imglogs(ds_id)
                for ilog in img_log_list:
                    html = reader.get_mosaic_image(ilog.log_id, startsampleno=startsampleno, endsampleno=endsampleno,
                                                   width=width)
                    depth_list = reader.get_tray_depths(ilog.log_id)
                    yield n_id, ds_id, ilog, depth_list, html

