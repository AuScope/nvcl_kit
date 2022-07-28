#!/usr/bin/env python3
import sys
from types import SimpleNamespace
from nvcl_kit.reader import NVCLReader
import yaml

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
# ./demo.py
#
#

# Provider list. Format is (WFS service URL, NVCL service URL, bounding box coords, borehole crs, local filtering, WFS version, max boreholes))
prov_list = [ ("https://www.mrt.tas.gov.au/web-services/ows", "https://www.mrt.tas.gov.au/NVCLDataServices/", { "west": 143.75, "south": -43.75, "east": 148.75, "north": -39.75 }, None, False, "1.1.0", 20),
              ("https://geology.data.vic.gov.au/nvcl/ows", "https://geology.data.vic.gov.au/NVCLDataServices/", { "south": 100100, "north": 315000, "west": 5720750, "east": 6093000 }, "EPSG:28355", False, "1.1.0", 20),
             ("https://gs.geoscience.nsw.gov.au/geoserver/ows", "https://nvcl.geoscience.nsw.gov.au/NVCLDataServices/", None, None, False, "1.1.0", 20),
             ("https://geology.information.qld.gov.au/geoserver/ows", "https://geology.information.qld.gov.au/NVCLDataServices/", None, None, False, "1.1.0", 20),
             ("http://geology.data.nt.gov.au/geoserver/ows", "http://geology.data.nt.gov.au/NVCLDataServices/", None, None, True, "2.0.0", 20),
             ("https://sarigdata.pir.sa.gov.au/geoserver/ows", "https://sarigdata.pir.sa.gov.au/nvcl/NVCLDataServices/",None, None, False, "1.1.0", 20),
             # NB: Western Australia's DMIRS only supports WFS v2.0.0
             ("https://geossdi.dmp.wa.gov.au/services/ows",  "https://geossdi.dmp.wa.gov.au/NVCLDataServices/", None, None, False, "2.0.0", 20)
]


def do_demo(wfs, nvcl, bbox, borehole_crs, local_filt, version, max):
    print("\n\n***", wfs, "***\n")

    # Assemble parameters
    param = SimpleNamespace()
    # NB: If you set USE_LOCAL_FILTERING to true then WFS_VERSION must be 2.0.0
    param.USE_LOCAL_FILTERING = local_filt
    param.WFS_URL = wfs
    param.WFS_VERSION = version
    param.NVCL_URL = nvcl
    if bbox is not None:
        param.BBOX= bbox
    if borehole_crs is not None:
        param.BOREHOLE_CRS = borehole_crs

    param.MAX_BOREHOLES = max

    # Initialise reader
    reader = NVCLReader(param)

    # Check for failure
    if not reader.wfs:
        print("ERROR!", wfs, nvcl)

    # Get boreholes list
    bh_list = reader.get_boreholes_list()
    print("len(bh_list) = ", len(bh_list))

    # Get list of NVCL ids
    nvcl_id_list = reader.get_nvcl_id_list()
    print("len(nvcl_id_list) = ", len(nvcl_id_list))
    print("nvcl_id_list[:5] = ", nvcl_id_list[:5])

    # Exit if no nvcl ids found
    if not nvcl_id_list:
        print("!!!! No NVCL ids for", nvcl)
        return

    # Some nvcl ids do not have any data - find the first which has data
    imagelog_data_list = []
    nvcl_id = ""
    for n_id in nvcl_id_list:
        imagelog_data_list = reader.get_imagelog_data(n_id)
        if imagelog_data_list:
            nvcl_id = n_id
            break

    # Exit if couldn't find valid data
    if not imagelog_data_list:
        print("!!!! No NVCL data for", nvcl)
        return

    for ild in imagelog_data_list[:10]:
        print(ild.log_id,
              ild.log_name,
              ild.log_type,
              ild.algorithmout_id)

    # Analysis class has 2 parts:
    # 1. Min1,2,3 = 1st, 2nd, 3rd most common mineral
    #    OR Grp1,2,3 = 1st, 2nd, 3rd most common group of minerals
    # 2. uTSAV = visible light, uTSAS = shortwave IR, uTSAT = thermal IR
    #
    # These combine to give us a class name such as 'Grp1 uTSAS'
    #
    # Here we extract data for log type '1' and 'Grp1 uTSAS'
    HEIGHT_RESOLUTION = 20.0
    ANALYSIS_CLASS = 'Grp1 uTSAS'
    LOG_TYPE = '1'
    for ild in imagelog_data_list[:10]:
        if ild.log_type == LOG_TYPE and ild.log_name == ANALYSIS_CLASS:
            print('get_borehole_data()')
            # Get top 5 minerals at each depth
            bh_data = reader.get_borehole_data(ild.log_id, HEIGHT_RESOLUTION, ANALYSIS_CLASS, top_n=5)
            for depth in bh_data:
                for meas in bh_data[depth]:
                    print("At {} metres: class={}, abundance={}, mineral={}, colour={}".format(depth, meas.className,
                      meas.classCount, meas.classText, meas.colour))
                print()

    print('get_profilometer_data()')
    profilometer_data_list = reader.get_profilometer_data(nvcl_id)
    for pdl in profilometer_data_list[:10]:
        print(pdl.log_id,
              pdl.log_name,
              pdl.max_val,
              pdl.min_val,
              pdl.floats_per_sample,
              pdl.sample_count)

    print('get_dataset_list()')
    dataset_list = reader.get_dataset_list(nvcl_id)
    for dataset in dataset_list[:10]:
        print(dataset.dataset_id,
              dataset.dataset_name,
              dataset.borehole_uri,
              dataset.tray_id,
              dataset.section_id,
              dataset.domain_id)

    print('get_datasetid_list()')
    datasetid_list = reader.get_datasetid_list(nvcl_id)
    for dataset_id in datasetid_list[:5]:
        print('dataset_id:', dataset_id)

        # GET_MOSAIC_IMGLOGS, GET_MOSAIC_IMAGE
        img_log_list = reader.get_mosaic_imglogs(dataset_id)
        print('get_mosaic_imglogs() ', img_log_list)
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

    # GET_SPECTRAL_DATA
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

    # GET_SPECTRAL_DATASETS
    log_id_list = [sld.log_id for sld in spectrallog_data_list][:10]
    for sl_log in log_id_list:
             sl_bin = reader.get_spectrallog_datasets(sl_log, start_sample_no="0", end_sample_no="2")
             print('get_spectral_datasets()', repr(sl_bin)[:50])



#
# MAIN PART OF SCRIPT
#
if __name__ == "__main__":

    # Loop over all the providers
    for prov_info in prov_list:
        do_demo(*prov_info)

