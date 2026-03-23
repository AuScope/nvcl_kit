'''
A collection of generator functions to make it easy to create scalar datasets, core images and plots
'''

from io import StringIO
import logging
import sys
from typing import Iterator, List, Union

import pandas as pd

from nvcl_kit.constants import Scalar
from nvcl_kit.df import to_summary
from nvcl_kit.reader import NVCLReader

# Set up debugging
LOG_LVL = logging.INFO
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(LOG_LVL)

if not LOGGER.hasHandlers():
    # Create logging console handler
    HANDLER = logging.StreamHandler(sys.stdout)

    # Create logging formatter
    FORMATTER = logging.Formatter(
        "%(name)s -- %(levelname)s - %(funcName)s: %(message)s"
    )

    # Add formatter to ch
    HANDLER.setFormatter(FORMATTER)

    # Add handler to LOGGER and set level
    LOGGER.addHandler(HANDLER)

def list_scalar_names(scalar_set="sTSAS", scalar_level="Group") -> List[str]:
    """
    Returns a list of scalar names based on the scalar level & scalar set.

    e.g. ["Grp1 sTSAS", "Grp2 sTSAS", "Grp3 sTSAS"]

    Args:
        scala_set (str, optional): e.g. "sTSAS", "sjCLST", "uTSAT", etc. Defaults to "sTSAS".
        scalar_level (str, optional): "group" or "mineral". Defaults to "Group".

    Returns:
        List[str]: List of scalar names
    """
    if scalar_level.lower() in ("group", "grp"):
        scalar_levels = ["Grp1", "Grp2", "Grp3"]
    elif scalar_level.lower() in ("mineral", "min"):
        scalar_levels = ["Min1", "Min2", "Min3"]
    else:
        raise ValueError("Scalar level must be 'Group', or 'Mineral'.")
    return [" ".join([p, scalar_set]) for p in scalar_levels]


def list_scalar_weights(scalar_set="sTSAS") -> List[str]:
    """
    Returns a list of scalar weight names based on the scalar set.

    e.g. ["Wt1 sTSAS", "Wt2 sTSAS", "Wt3 sTSAS"]

    Args:
        scala_set (str, optional): e.g. "sTSAS", "sjCLST", "uTSAT", etc. Defaults to "sTSAS".

    Returns:
        List[str]: List of scalar names
    """
    return [" ".join([p, scalar_set]) for p in ["Wt1", "Wt2", "Wt3"]]


def gen_summary_dataframe(
    reader: NVCLReader,
    *,
    nvcl_id_list: List[str] = None,
    resolution: Union[float, None] = 1.0,
    start_depth="floor",
    scalar_set="sTSAS",
    scalar_level="Group",
    weighted=True,
    percent=True,
    min_item_wt: Union[float, None] = None,
    min_item_pct: Union[float, None] = None,
    max_item_pct: Union[float, None] = None,
    concat_data=False,
    include_srss=False,
    include_snr=False,
    continue_on_error=False,
    continue_on_missing=False,
) -> Iterator[dict|pd.DataFrame]:
    """
    Yields summary data for a given scalar for each borehole as `pd.DataFrame`s

    The start_depth values can be configured to start at a whole number ('floor'), rounded
    to 2 places ('round'), or to start from the first depth ('min' or None). Has no effect if
    `resolution` is None.

    The `continue_on_missing` flag allows you to try and download a scalar set/level without
    knowing if it actually exists. Useful in batch download scenarios where not all holes contain
    all the scalars.

    Example:
    ```
    meta, df = next(gen_summary_dataframe(reader=reader, nvcl_id_list=["MIN_027902"]))
    ```

    Args:
        reader (NVCLReader): NVCLReader client
        nvcl_id_list (List[str], optional): List of NVCL IDs. Defaults to None.
        resolution (Union[float, None], optional): Depth for binning data, set to None to skip. Defaults to 1.0.
        start_depth (str, optional): Can be 'floor', 'round', 'min' or `None`. Defaults to "floor".
        scalar_set (str, optional):  'sTSAS', 'sTSAT', 'uTSAS', etc. Defaults to "sTSAS".
        scalar_level (str, optional): "Group" or "Mineral". Defaults to "Group".
        weighted (bool, optional): Bin by relative weight when True, else Sample count. Defaults to True.
        percent (bool, optional): Convert columns to percentage. Defaults to True.
        min_item_wt (Union[float, None], optional): Only includes scalars > min weight. Defaults to None.
        min_item_pct (Union[float, None], optional): Only includes scalars > min %. Defaults to None.
        max_item_pct (Union[float, None], optional): Only includes scalars < max %. Defaults to None.
        concat_data (bool, optional): Combine holes into single dataframe otherwise one per hole. Defaults to False.
        include_srss (bool, optional): Include the Standardised residual sum of squares (TSA's measure of mineral identification error). Defaults to False.
        include_snr (bool, optional): Include signal-to-noise ratio. Defaults to False.
        continue_on_error (bool, optional): Ignore errors and charge forth. Defaults to False.
        continue_on_missing (bool, optional): Skip scalars if they're missing. Defaults to False.

    Yields:
        Iterator[dict|pd.DataFrame]: dataframe containing summary data for selected scalar
    """
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list()
        if not nvcl_id_list:
            raise StopIteration()

    # Retrieve the algorithm dictionary for reference
    algo_dict = reader.get_algorithms()

    # Prepare a dataframe for each borehole
    df_list = []
    df_meta_list = []

    for n_id in nvcl_id_list:
        logs_data_list = reader.get_logs_data(n_id, last_only=True)
        LOGGER.debug(f"NVCL ID: {n_id}, found {len(logs_data_list)} logs")

        if not logs_data_list:
            continue

        # Note: If we want raw counts the same value may appear in multiple mixture levels.
        # Build list of scalar data to download
        scalar_names = list_scalar_names(
            scalar_set=scalar_set, scalar_level=scalar_level
        )
        # if !weighted then ignore Wt{1-3} scalars
        wt_names = list_scalar_weights(scalar_set=scalar_set) if weighted else []

        # Pull out all the scalar log ids we need to download
        scalar_ids = []
        found_scalars = []
        found_wt = []
        df_meta = {
            "borehole_uri": n_id,
            "weighted": weighted,
            "resolution": resolution,
            "scalar_set": scalar_set,
            "scalar_level": scalar_level,
            "scalar_algorithm_version": "Unknown",
            "min_item_wt": min_item_wt,
            "min_item_pct": min_item_pct,
            "max_item_pct": max_item_pct,
            }
        
        # You can have multiple logs with the same log_name, but different algorithm_id's. 
        # Need to filter so we only keep highest algorithm version.
        max_algo_id = dict()
        for ld in logs_data_list:
            if ld.log_name in scalar_names or ld.log_name in wt_names:
                if ld.log_name not in max_algo_id or int(ld.algorithm_id) > int(max_algo_id[ld.log_name]):
                    max_algo_id[ld.log_name] = ld.algorithm_id

        for ld in logs_data_list:
            if ld.log_name == f"Error {scalar_set}" and include_srss:
                LOGGER.debug(f"NVCL ID: {n_id}, Error metric (SNSS) found [{ld.log_name}]")
                scalar_ids.append(ld.log_id)
                continue
            
            if ld.log_name == f"SNR {scalar_set}" and include_snr:
                LOGGER.debug(f"NVCL ID: {n_id}, SNR found [{ld.log_name}]")
                scalar_ids.append(ld.log_id)
                continue

            if ld.log_name in scalar_names:
                scalar_ids.append(ld.log_id)
                found_scalars.append(ld.log_name)
                if df_meta["scalar_algorithm_version"] == "Unknown":
                    df_meta["scalar_algorithm_version"] = algo_dict.get(ld.algorithm_id, "Unknown")
                    df_meta["classifications"] = reader.get_classifications(log_id=ld.log_id)
                continue

            if ld.log_name in wt_names:
                scalar_ids.append(ld.log_id)
                found_wt.append(ld.log_name)
        LOGGER.debug(f"NVCL ID: {n_id}, found scalars: {found_scalars}, found weights: {found_wt}")

        # If the requests scalars can't be found throw an error or skip
        if len(scalar_ids) < 1:
            if continue_on_missing:
                continue
            else:
                raise KeyError(
                    f"NVCL ID: {n_id}, does not have the requested scalars {scalar_names}!"
                )

        # Fetch scalars and load into pandas
        bh_data = reader.get_scalar_data(scalar_ids)
        if isinstance(bh_data, bytes) and len(bh_data) > 0:
            bh_data = bh_data.decode("utf-8")
        elif continue_on_error:
            continue
        else:
            raise RuntimeError(
                f"Request to download scalar data failed! (NVCL ID: {n_id})"
            )

        try:
            # Convert the CSV string to a DataFrame
            df = pd.read_csv(StringIO(bh_data))
            LOGGER.debug(f"NVCL ID: {n_id}, downloaded scalar data with the coloumns: {df}")
            # Convert the scalar data into a summary view
            df = to_summary(
                df,
                scalar_cols=found_scalars,
                wt_cols=found_wt,
                nvcl_id=n_id,
                start_depth=start_depth,
                resolution=resolution,
                percent=percent,
                min_item_wt=min_item_wt,
                min_item_pct=min_item_pct,
                max_item_pct=max_item_pct,
            )
        except Exception as e:
            if continue_on_error:
                continue
            else:
                raise e

        if concat_data:
            # defer yielding until we've concatenated all the holes together
            df_list.append(df)
            df_meta_list.append(df_meta)
        else:
            yield df_meta, df

    if concat_data:
        yield df_meta_list, pd.concat(df_list)
    else:
        # If the function didn't already yield then it means there was no dataframe
        # so return to stop iterating.
        return


def gen_scalar_by_depth(
    reader,
    *,
    nvcl_id_list=None,
    resolution=20.0,
    scalar_class=Scalar.ANY,
    log_type=None,
    top_n=5,
    remove_invalid=True,
):
    """Returns scalar borehole data ordered by depth given filter parameters

    :param nvcl_id_list: optional list of nvcl ids
    :param resolution: optional nvcl_kit.constants.Scalar class object, default Scalar.ANY
    :param log_type: optional log type e.g. '1' or '2'
    :param top_n: optional, only retrieve the first n scalara at each depth, default  value is 5
    :return: yields a tuple of (nvcl_id, logs object, scalar data object); logs object is retrieved from 'get_logs_data()'
    """
    if nvcl_id_list is None:
        nvcl_id_list = reader.get_nvcl_id_list()
        if not nvcl_id_list:
            raise StopIteration()

    for n_id in nvcl_id_list:
        logs_data_list = reader.get_logs_data(n_id)
        if logs_data_list:
            for ld in logs_data_list:
                if (
                    log_type is None
                    or (hasattr(ld, "log_type") and ld.log_type == log_type)
                ) and (ld.log_name == scalar_class or scalar_class == Scalar.ANY):
                    scalar_data = reader.get_borehole_data(
                        ld.log_id,
                        resolution,
                        ld.log_name,
                        top_n=top_n,
                        remove_invalid=remove_invalid,
                    )
                    yield n_id, ld, scalar_data


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

    for n_id in nvcl_id_list:
        datasetid_list = reader.get_datasetid_list(n_id)
        if datasetid_list:
            for ds_id in datasetid_list:
                img_log_list = reader.get_imagery_imglogs(ds_id)
                for ilog in img_log_list:
                    if max_magnify:
                        html = reader.get_mosaic_image(ilog.log_id, startsampleno=startsampleno,
                                                       endsampleno=endsampleno, width=1)
                    else:
                        html = reader.get_mosaic_image(ilog.log_id, startsampleno=startsampleno,
                                                       endsampleno=endsampleno)
                    depth_list = reader.get_tray_depths(ilog.log_id)
                    yield n_id, ds_id, ilog, depth_list, html

