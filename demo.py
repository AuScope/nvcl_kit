#!/usr/bin/env python3
import sys
from types import SimpleNamespace
import yaml

from nvcl_kit.reader import NVCLReader
from nvcl_kit.param_builder import param_builder
from nvcl_kit.constants import Scalar
from nvcl_kit.generators import gen_scalar_by_depth


#
# A very rough script to demonstrate 'nvcl_kit' 
#
# Linux command line instructions:
#
# git clone https://gitlab.com/csiro-geoanalytics/python-shared/nvcl_kit.git
# cd nvcl_kit
# mkdir venv
# python3 -m venv ./venv
# . ./venv/bin/activate
# pip install -U pip
# pip install -r requirements.txt
# ./demo_new.py
#
#

state_list = ['csiro', 'nsw', 'tas', 'vic', 'qld', 'sa', 'wa', 'nt']

def do_demo(state):
    print(f"\n\n*** {state} ***\n")

    # Assemble parameters
    #     First parameter is state or territory name, one of: 'nsw', 'tas', 'vic', 'qld', 'nt', 'sa', 'wa'
    #     Other parameters are optional:
    #               bbox: 2D bounding box in EPSG:4326, only boreholes within box are retrieved
    #                     default {"west": -180.0,"south": -90.0,"east": 180.0,"north": 0.0})
    #               polygon: 2D 'shapely.geometry.LinearRing' object, only boreholes within this ring are retrieved
    #               borehole_crs: CRS string, default "EPSG:4326"
    #               wfs_version: WFS version string, default "1.1.0"
    #               depths: Tuple of range of depths (min,max) [metres]
    #               wfs_url: URL of WFS service, GeoSciML V4.1 BoreholeView
    #               nvcl_url: URL of NVCL service
    #               max_boreholes: Maximum number of boreholes to retrieve. If < 1 then all boreholes are loaded
    #                              default 0
    param = param_builder(state, max_boreholes=20)
    if not param:
        print(f"Cannot build parameters: {param}")
        return

    # Initialise reader
    reader = NVCLReader(param)
    if not reader.wfs:
        print(f"ERROR! Cannot contact WFS service for {state}")
        return

    # Get WFS borehole feature list
    bh_list = reader.get_feature_list()

    # Filter features by name or other attributes
    if state == 'tas':
        brd005_list = reader.filter_feat_list(name='BRD005')
        print(f"Details of BRD005: {brd005_list}")

    # Print first 5 WFS borehole features
    for bh in bh_list[:5]:
        print("\nBOREHOLE:")
        print(bh)

    # Get list of NVCL ids
    nvcl_id_list = reader.get_nvcl_id_list()

    # Exit if no nvcl ids found
    if not nvcl_id_list:
        print(f"ERROR! No NVCL ids for {state}")
        return

    # The names of NVCL scalar classes have 3 parts; first part is class grouping type, 
    # second is the TSA mineral matching technique, third part is wavelength:
    #  1. Min1,2,3 = 1st, 2nd, 3rd most common mineral type
    #     OR Grp1,2,3 = 1st, 2nd, 3rd most common group of minerals
    #  2. uTSA = user, dTSA = domaining, sTSA = system
    #  3. V = visible light, S = shortwave IR, T = thermal IR
    #
    # These combine to give us a class name such as 'Grp1 uTSAS'
    #
    # Here we extract data for 'Grp1 uTSAS' using 'Scalar' class
    #
    # GEN_SCALAR_BY_DEPTH
    for nvcl_id, log_id, sca_list in gen_scalar_by_depth(reader, scalar_class=Scalar.Grp1_uTSAS, log_type='1', top_n=4):
        for depth in sca_list:
            for meas in sca_list[depth]:
                print(f"{nvcl_id} {log_id} @ {depth} metres: class={meas.className}, abundance={meas.classCount}, mineral={meas.classText}, colour={meas.colour}")
            print()

    # GET_DATASET_LIST
    print('get_dataset_list()')
    nvcl_id = nvcl_id_list[0]
    dataset_list = reader.get_dataset_list(nvcl_id)
    for dataset in dataset_list[:10]:
        print(dataset.dataset_id,
              dataset.dataset_name,
              dataset.borehole_uri,
              dataset.tray_id,
              dataset.section_id,
              dataset.domain_id)

    # GET_DATASETID_LIST
    print('get_datasetid_list()')
    datasetid_list = reader.get_datasetid_list(nvcl_id)
    for dataset_id in datasetid_list[:5]:
        print(f"dataset_id: {dataset_id}")

        # GET_MOSAIC_IMGLOGS, GET_MOSAIC_IMAGE
        img_log_list = reader.get_mosaic_imglogs(dataset_id)
        print(f"get_mosaic_imglogs() {img_log_list}")
        for img_log in img_log_list[:10]:
            print(img_log.log_id,
                  img_log.log_name,
                  img_log.sample_count)
            html = reader.get_mosaic_image(img_log.log_id)
            print('get_mosaic_image()', repr(html[:4000]))


        # GET_TRAY_THUMBNAIL_IMGLOGS, GET_TRAY_THUMB_HTML, GET_TRAY_THUMB_JPG
        # & GET_TRAY_DEPTHS
        print('get_tray_thumb_imglogs()')
        img_log_list = reader.get_tray_thumb_imglogs(dataset_id)
        for img_log in img_log_list[:10]:
            print(img_log.log_id,
                  img_log.log_name,
                  img_log.sample_count)
            html = reader.get_tray_thumb_html(dataset_id, img_log.log_id)
            print('get_tray_thumb_html()', html[:400])
            jpg = reader.get_tray_thumb_jpg(img_log.log_id)
            print('get_tray_thumb_jpg()', repr(jpg)[:100])
            depth_list = reader.get_tray_depths(img_log.log_id)
            print('get_tray_depths():')
            for depth in depth_list[:10]:
                print(depth.sample_no,
                      depth.start_value,
                      depth.end_value)


        # GET_TRAY_IMGLOGS, GET_TRAY_THUMB_HTML & GET_TRAY_DEPTHS
        print('get_tray_imglogs()')
        img_log_list = reader.get_tray_imglogs(dataset_id)
        for img_log in img_log_list[:10]:
            print(img_log.log_id,
                  img_log.log_name,
                  img_log.sample_count)
            html = reader.get_tray_thumb_html(dataset_id, img_log.log_id)
            print('get_tray_thumb_html()', html[:400])
            depth_list = reader.get_tray_depths(img_log.log_id)
            print('get_tray_depths():')
            for depth in depth_list[:10]:
                print(depth.sample_no,
                      depth.start_value,
                      depth.end_value)

        # GET_IMAGERY_IMGLOGS
        print('get_imagery_imglogs()')
        img_log_list = reader.get_imagery_imglogs(dataset_id)
        for img_log in img_log_list[:10]:
            print(img_log.log_id,
                  img_log.log_name,
                  img_log.sample_count)
            print('get_imagery_logs()', html[:400])


        # GET_SCALAR_LOGS & PLOT_SCALAR_PNG
        print('get_scalar_logs()')
        scalar_log_list = reader.get_scalar_logs(dataset_id)
        for scalar_log in scalar_log_list[:10]:
            print(scalar_log.log_id,
                  scalar_log.log_name)
            png = reader.plot_scalar_png(scalar_log.log_id)
            print('plot_scalar_png()', repr(png)[:100])


        # PLOT_SCALARS_HTML
        log_id_list = [scalar_log.log_id for scalar_log in scalar_log_list]
        html = reader.plot_scalars_html(log_id_list)
        print('plot_scalars_html()', html[:400])


        # GET_SCALAR_LOGS & GET_SCALAR_DATA
        sca_log_list = reader.get_scalar_logs(dataset_id)
        print('get_scalar_logs()', sca_log_list[:10])
        log_id_list = [sca_log.log_id for sca_log in sca_log_list][:4]
        csv = reader.get_scalar_data(log_id_list)
        print('get_scalar_data()', csv[:400])


        # GET_SAMPLED_SCALAR_DATA
        for sca_log in sca_log_list[:5]:
            sampled_data = reader.get_sampled_scalar_data(sca_log.log_id,
                                                     outputformat='json',
                                                     startdepth=0,
                                                     enddepth=2000,
                                                     interval=100)
            print('get_sampled_scalar_data()', sampled_data[:400])

    # GET_PROFILOMETER_DATA
    print('get_profilometer_data()')
    profilometer_data_list = reader.get_profilometer_data(nvcl_id)
    for pdl in profilometer_data_list[:10]:
        print(pdl.log_id,
              pdl.log_name,
              pdl.max_val,
              pdl.min_val,
              pdl.floats_per_sample,
              pdl.sample_count)

    # GET_SPECTRALLOG_DATA
    print('get_spectrallog_data()')
    spectrallog_data_list = reader.get_spectrallog_data(nvcl_id)
    for sld in spectrallog_data_list[:2]:
        print(sld.log_id,
              sld.log_name,
              sld.wavelength_units,
              sld.sample_count,
              sld.script,
              sld.script_raw,
              sld.wavelengths)

    # GET_SPECTRALLOG_DATASETS
    log_id_list = [sld.log_id for sld in spectrallog_data_list][:10]
    for sl_log in log_id_list:
             sl_bin = reader.get_spectrallog_datasets(sl_log, start_sample_no="0", end_sample_no="2")
             print('get_spectrallog_datasets()', repr(sl_bin)[:50])



#
# MAIN PART OF SCRIPT
#
if __name__ == "__main__":

    # Loop over all the providers
    for state in state_list:
        do_demo(state)

