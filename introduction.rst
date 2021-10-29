Introduction: How to Extract Australian NVCL Borehole Data
----------------------------------------------------------

**1. Call the 'param_builder' function, fill it with parameters**

.. code:: python

    from nvcl_kit.reader import NVCLReader
    from nvcl_kit.param_builder import param_builder
    from nvcl_kit.constants import Scalar
    from nvcl_kit.generators import gen_scalar_by_depth
 
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
    param = param_builder('nsw', max_boreholes=20)
    if not param:
        print(f"Cannot build parameters: {param}")



**2. Create 'NVCLReader' class, check if 'wfs' is not 'None' to see if this instance initialised correctly
properly**

.. code:: python

    # Instantiate class and search for boreholes
    reader = NVCLReader(param)
    if not reader.wfs:
        print("ERROR!")

**3. Call get\_feature\_list() to get list of WFS borehole data for
NVCL boreholes or use 'filter_feat_list() to narrow down the list**

.. code:: python

    # Returns a list of python 'SimpleNamespace' objects (from 'types' module)
    # Each object has fields from GeoSciML v4.1 BoreholeView
    # accessed using '.' notation e.g. 'bh_list[0].name'
    bh_list = reader.get_feature_list()

    # Feature lists can be filtered by name and other attributes
    feat_list = reader.filter_feat_list(name='BRD005')
    print(feat_list)

**4. Call get\_nvcl\_id\_list() to get a list of NVCL borehole ids**

.. code:: python

    nvcl_id_list = reader.get_nvcl_id_list()

**5. Using an NVCL borehole id from previous step, call
get\_imagelog\_data() to get the NVCL log ids**

.. code:: python

    # Get list of NVCL log ids
    nvcl_id_list = reader.get_nvcl_id_list()

    # Get NVCL log id for first borehole in list
    nvcl_id = nvcl_id_list[0]

    # Get image log data for first borehole
    imagelog_data_list = reader.get_imagelog_data(nvcl_id)
    for ild in imagelog_data_list:
        print(ild.log_id,
              ild.log_name,
              ild.log_type,
              ild.algorithmout_id)

**6. Using image log data, call gen\_scalar\_by\_depth() to get borehole scalar data**

.. code:: python

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

**7. Using the NVCL id from Step 5, you can also call
get\_spectrallog\_data() and get\_profilometer\_data()**

.. code:: python

    spectrallog_data_list = reader.get_spectrallog_data(nvcl_id)
    for sld in spectrallog_data_list:
        print(sld.log_id,
              sld.log_name,
              sld.wavelength_units,
              sld.sample_count,
              sld.script,
              sld.script_raw,
              sld.wavelengths)

    profilometer_data_list = reader.get_profilometer_data(nvcl_id)
    for pdl in profilometer_data_list:
        print(pdl.log_id,
              pdl.log_name,
              pdl.max_val,
              pdl.min_val,
              pdl.floats_per_sample,
              pdl.sample_count)

**8. Option: get a list of dataset ids**

.. code:: python

    datasetid_list = reader.get_datasetid_list(nvcl_id)

**9. Option: Get a list of datasets**

.. code:: python

    dataset_list = reader.get_dataset_list(nvcl_id)
    for ds in dataset_list:
        print(ds.dataset_id,
              ds.dataset_name,
              ds.borehole_uri,
              ds.tray_id,
              ds.section_id,
              ds.domain_id)

**10. Using an element from 'datasetid\_list' in Step 8 or
'ds.dataset\_id' from Step 9, can retrieve log data**

.. code:: python

    # Scalar log data
    log_list = reader.get_scalar_logs(ds.dataset_id)
    for log in log_list:
        print(log.log_id,
              log.log_name,
              log.is_public,
              log.log_type,
              log.algorithm_id)

.. code:: python

    # Different types of image log data
    ilog_list = reader.get_all_imglogs(ds.dataset_id)
    ilog_list = reader.get_mosaic_imglogs(ds.dataset_id)
    ilog_list = reader.get_tray_thumb_imglogs(ds.dataset_id)
    ilog_list = reader.get_tray_imglogs(ds.dataset_id)
    ilog_list = reader.get_imagery_imglogs(ds.dataset_id)

    for ilog in ilog_list:
        print(ilog.log_id,
              ilog.log_name,
              ilog.sample_count)

**11. Using the scalar log ids, can get scalar data and plots of scalar
data**

.. code:: python

    # Scalar data in CSV format
    log_id_list = [l.log_id for l in log_list]
    data = reader.get_scalar_data(log_id_list)

    # Sampled scalar data in JSON (or CSV) format
    samples = reader.get_sampled_scalar_data(log.log_id,
                                             outputformat='json',
                                             startdepth=0,
                                             enddepth=2000,
                                             interval=100)

    # A data plot in PNG
    plot_data = reader.plot_scalar_png(log_id)

    # Data plots in HTML, only plots the first 6 log ids
    plot_data = reader.plot_scalars_html(log_id_list)

**12. Using the image log ids can produce images of NVCL cores**

.. code:: python

    ilog_list = reader.get_mosaic_imglogs(ds.dataset_id)
    for ilog in ilog_list:
        img = reader.get_mosaic_image(ilog.log_id)

    ilog_list = reader.get_tray_thumb_imglogs(ds.dataset_id)
    for ilog in ilog_list:
        # Either HTML or JPG
        img = reader.get_tray_thumb_html(ds.dataset_id, ilog.log_id)
        img = reader.get_tray_thumb_jpg(ilog.log_id)

    # Use either 'get_tray_thumb_imglogs()' or 'get_tray_imglogs()'
    ilog_list = reader.get_tray_thumb_imglogs(ds.dataset_id)
    ilog_list = reader.get_tray_imglogs(ds.dataset_id)
    for ilog in ilog_list:
        depth_list = reader.get_tray_depths(ilog.log_id)
        for depth in depth_list:
            print(depth.sample_no,
                  depth.start_value,
                  depth.end_value)

