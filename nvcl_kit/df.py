"""Functions for working with NVCL data using pandas DataFrames"""

import logging
import sys
from math import floor
from typing import List, Optional, Union

import numpy as np
import pandas as pd

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

def to_summary(
    df: pd.DataFrame,
    scalar_cols: List[str],
    wt_cols: Optional[List[str]] = None,
    nvcl_id: Optional[str] = None,
    start_depth="floor",
    resolution: Union[float, None] = 1.0,
    percent=True,
    min_item_wt: Union[float, None] = None,
    min_item_pct: Union[float, None] = None,
    max_item_pct: Union[float, None] = None,
) -> pd.DataFrame:
    """
    Returns a DataFrame containing a summary view of scalar data.

    The summary values will be weighted unless `wt_cols` is `None` in which case the
    counts will be returned.

    The start_depth values can be configured to start at a whole number ('floor'), rounded
    to 2 places ('round'), or to start from the first depth ('min' or None). Has no effect if
    `resolution` is None.

    :param pd.DataFrame df: DataFrame containing scalar data (from reader.get_scalar_data(...))
    :param List[str] scalar_cols: List of column names containing the scalars.
    :param wt_cols (Optional[List[str]]): List of column names containing weights.
    :param nvcl_id (Optional[str]): The borehole identifier to include in the returned dataframe.
    :param str start_depth: Can be 'floor', 'round', 'min' or `None`. Defaults to "floor". (Optional)
    :param Union[float, None] resolution: Depth for binning data, set to None to skip. Defaults to 1.0. (Optional)
    :param bool percent: Convert columns to percentage. Defaults to True. (Optional)
    :param Union[float, None] min_item_wt: Only includes scalars > min weight. Defaults to None. (Optional)
    :param Union[float, None] min_item_pct: Only includes scalars > min %. Defaults to None. (Optional)
    :param Union[float, None] max_item_pct: Only includes scalars < max %. Defaults to None. (Optional)

    :return: dataframe containing summary of scalar data
    :rtype: pd.DataFrame
    """
    # Convert scalar column names to match those in dataframe and sort
    # them to match the sorted scalar columns
    scalar_cols = [s.replace(" ", "_") for s in scalar_cols]
    scalar_cols.sort()

    # Pivot the scalars into wide format
    pivoted_dfs = []
    if isinstance(wt_cols, list) and len(wt_cols) > 0:
        if len(scalar_cols) != len(wt_cols):
            raise ValueError(
                "Number of weight columns does not match number of scalars"
            )
        # Convert weight column names to match those in dataframe and sort
        # them to match the sorted scalar columns
        wt_cols = [w.replace(" ", "_") for w in wt_cols]
        wt_cols.sort()

        # summarise by weight
        for s, wt in list(zip(scalar_cols, wt_cols)):
            LOGGER.debug(f"Processing scalar {s} with weights {wt}")
            # Verify that the weights are available
            if s in df.columns and wt not in df.columns:
                raise KeyError(f"Unable to find weights for {s}")

            # Zero out weights BELOW the threshold
            if isinstance(min_item_wt, (float, int)):
                # Check the min_item_wt is valid
                if min_item_wt < 0 or min_item_wt > 1:
                    raise ValueError("min_item_wt must be between 0.0 and 1.0")

                df.loc[df[wt] < min_item_wt, wt] = 0.0
            pivoted_dfs.append(
                df.pivot_table(
                    index=["StartDepth"], columns=s, values=wt, aggfunc="sum"
                )
            )
    else:
        # Summarise by count
        for s in scalar_cols:
            pivoted_dfs.append(
                df.pivot_table(
                    index="StartDepth",
                    values=[],
                    columns=s,
                    aggfunc=lambda x: 1.0,
                    fill_value=np.nan,
                )
            )

    # Find any columns in df which begin with "SNR_" or "Error_"
    snr_error_cols = [col for col in df.columns if col.startswith("SNR_") or col.startswith("Error_")]
    snr_error_dfs = []
    for s in snr_error_cols:
        snr_error_dfs.append(df[[s]].groupby(df['StartDepth']).last())
    
    # Each scalar (e.g. sTSAS) and each level (e.g. Grp1, Grp2, Grp3) will now have its
    # own dataframe which all need to be merged together. Once done the separate levels
    # for each scalar should be summed together.
    df = pd.concat(pivoted_dfs, axis="columns").reset_index()
    df = df.T.groupby(by=df.columns).sum().T
    class_names = list(df.columns)
    class_names.remove("StartDepth")

    # Add any SNR/Error columns to the dataframe
    if len(snr_error_dfs) > 0:
        LOGGER.debug("Adding SNR/Error column to summary:")
        snr_error_df = pd.concat(snr_error_dfs, axis="columns").reset_index()
        df = pd.merge(df, snr_error_df, on="StartDepth", how="left")
    
    
    # Bin the data unless `resolution` is `None`
    if isinstance(resolution, (int, float)):
        # configure bins to start at floor, rounded, min
        if start_depth == "floor":
            bin_start = floor(df["StartDepth"].min())
        elif start_depth == "min":
            bin_start = df["StartDepth"].min()
        elif start_depth == "round" or start_depth is None:
            bin_start = round(df["StartDepth"].min(), 2)
        else:
            raise ValueError("start_depth must be 'floor', 'min', or 'round'.")

        bin_edges = np.arange(
            bin_start,
            df["StartDepth"].max() + resolution,
            resolution,
        )
        df["depth_bin"] = pd.cut(
            df["StartDepth"], bins=bin_edges, right=False, precision=6
        )
        # Group by depth_bin, summing all columns except SNR/Error which are averaged
        sum_cols = df.columns.difference(snr_error_cols)
        sum_grp = df[sum_cols].groupby("depth_bin", observed=True).sum().reset_index()
        mean_grp = df[["depth_bin"]+snr_error_cols].groupby("depth_bin", observed=True).mean().reset_index()
        
        # Convert depth_bin categories to floats for StartDepth/EndDepth
        sum_grp["StartDepth"] = sum_grp["depth_bin"].apply(lambda x: x.left)
        sum_grp["StartDepth"] = sum_grp["StartDepth"].astype(float)
        sum_grp["EndDepth"] = sum_grp["depth_bin"].apply(lambda x: x.right)
        sum_grp["EndDepth"] = sum_grp["EndDepth"].astype(float)

        mean_grp["StartDepth"] = mean_grp["depth_bin"].apply(lambda x: x.left)
        mean_grp["StartDepth"] = mean_grp["StartDepth"].astype(float)
        mean_grp["EndDepth"] = mean_grp["depth_bin"].apply(lambda x: x.right)
        mean_grp["EndDepth"] = mean_grp["EndDepth"].astype(float)

        # drop the depth_bin column from both dataframes and merge them back together on StartDepth/EndDepth
        # N.B. you could merge on depth_bin but and then create the StartDepth/EndDepth columns but you
        #      will have pandas complain with "RuntimeWarning: invalid value encountered in cast"
        sum_grp = sum_grp.drop(columns=["depth_bin"])
        mean_grp = mean_grp.drop(columns=["depth_bin"])
        df = pd.merge(sum_grp, mean_grp, on=["StartDepth", "EndDepth"], how="left")

    else:
        df["EndDepth"] = df["StartDepth"]

    # Calculate totals across rows for use in filtering (below)
    df["total"] = df[class_names].sum(axis=1)

    # Zero out any class BELOW the minimum threshold
    if isinstance(min_item_pct, (float, int)):
        for cname in class_names:
            m = (df[cname] / df["total"] * 100) < min_item_pct
            df.loc[m, cname] = 0.0

    # Zero out any class ABOVE the minimum threshold
    if isinstance(max_item_pct, (float, int)):
        for cname in class_names:
            m = (df[cname] / df["total"] * 100) > max_item_pct
            df.loc[m, cname] = 0.0

    # When true convert the counts/weights to a percentage for each depth
    if percent:
        # recalculate total post-filtering
        df["total"] = df[class_names].sum(axis=1)
        for cname in class_names:
            df[cname] = df[cname] / df["total"] * 100

    # Put columns into a meaningful order
    ordered_cols = ["StartDepth", "EndDepth"]
    # ..add BoreholeID first if provided
    if nvcl_id:
        df["BoreholeID"] = nvcl_id
        ordered_cols = ["BoreholeID"] + ordered_cols
    # ..append SNR and Error columns next if any
    if len(snr_error_cols) > 0:
        ordered_cols += snr_error_cols
    # ..then the class names
    ordered_cols += class_names
    df = df[ordered_cols]

    return df
