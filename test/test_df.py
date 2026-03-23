#!/usr/bin/env python3
import unittest
from io import StringIO

import numpy as np
import pandas as pd
try:
    from helpers import setup_scalar_data
except ImportError:
    from .helpers import setup_scalar_data

from nvcl_kit.df import to_summary
from nvcl_kit.generators import (
    list_scalar_names,
    list_scalar_weights,
)


class TestDataFrameFunctions(unittest.TestCase):
    """
    Test nvcl_kit dataframe functions
    """

    def test_gen_summary_dataframe_columns(self):
        """Tests summary dataframe generator returns correct columns in a sensible order"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names)
        self.assertCountEqual(
            list(df.columns),
            [
                "StartDepth",
                "EndDepth",
                "AMPHIBOLE",
                "CARBONATE",
                "CHLORITE",
                "DARK-MICA",
                "EPIDOTE",
                "INVALID",
                "KAOLIN",
                "NOTAROK",
                "OTHER-ALOH",
                "SMECTITE",
                "SULPHATE",
                "TOURMALINE",
                "WHITE-MICA",
            ],
        )
        self.assertEqual(list(df.columns)[:2], ["StartDepth", "EndDepth"])

    def test_gen_summary_dataframe_nvcl_id(self):
        """Tests summary dataframe generator returns correct columns incl. NVCL identifier"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names, nvcl_id="MyBorehole0001")
        self.assertCountEqual(
            list(df.columns),
            [
                "StartDepth",
                "BoreholeID",
                "EndDepth",
                "AMPHIBOLE",
                "CARBONATE",
                "CHLORITE",
                "DARK-MICA",
                "EPIDOTE",
                "INVALID",
                "KAOLIN",
                "NOTAROK",
                "OTHER-ALOH",
                "SMECTITE",
                "SULPHATE",
                "TOURMALINE",
                "WHITE-MICA",
            ],
        )
        self.assertEqual(list(df.columns)[:3], ["BoreholeID", "StartDepth", "EndDepth"])

    def test_gen_summary_dataframe_unbinned(self):
        """Tests summary dataframe generator returns unbinned group classes"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names, resolution=None)
        # Check the unbinned data is the expected shape, with correct columns
        self.assertEqual(df.shape, (17941, 15))
        self.assertCountEqual(
            list(df.columns),
            [
                "StartDepth",
                "EndDepth",
                "AMPHIBOLE",
                "CARBONATE",
                "CHLORITE",
                "DARK-MICA",
                "EPIDOTE",
                "INVALID",
                "KAOLIN",
                "NOTAROK",
                "OTHER-ALOH",
                "SMECTITE",
                "SULPHATE",
                "TOURMALINE",
                "WHITE-MICA",
            ],
        )

    def test_gen_summary_dataframe_1m(self):
        """Tests summary dataframe generator returns group classes binned @ 1m"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names, resolution=1.0)
        self.assertEqual(df.shape, (157, 15))
        self.assertTrue(np.all(df["EndDepth"] - df["StartDepth"] == 1.0))
        self.assertTrue(np.all(df["StartDepth"].diff()[1:] == 1.0))

    def test_gen_summary_dataframe_floor(self):
        """Tests summary dataframe generator returns group classes binned @ 1m starting at floor(min_depth)"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names, start_depth="floor")
        self.assertEqual(df["StartDepth"].iloc[0], 12.0)

    def test_gen_summary_dataframe_min(self):
        """Tests summary dataframe generator returns group classes binned @ 1m starting at min(min_depth)"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names, start_depth="min")
        self.assertEqual(df["StartDepth"].iloc[0], 12.20974999999999966)

    def test_gen_summary_dataframe_round(self):
        """Tests summary dataframe generator returns group classes binned @ 1m starting at round(round, 2)"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = to_summary(df, scalar_cols=scalar_names, start_depth="round")
        self.assertEqual(df["StartDepth"].iloc[0], 12.21)

    def test_gen_summary_dataframe_invalid_start_depth(self):
        """Tests summary dataframe generator raises an exception if start_depth is invalid"""
        scalar_names = list_scalar_names("sTSAS", "group")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        with self.assertRaisesRegex(
            ValueError, "start_depth must be 'floor', 'min', or 'round'"
        ):
            to_summary(df, scalar_cols=scalar_names, start_depth=1)

    def test_gen_summary_dataframe_missing_wt_in_df(self):
        """Tests summary dataframe generator raises an exception if start_depth is invalid"""
        scalar_names = list_scalar_names("sTSAS", "group")
        wt_names = list_scalar_weights("sTSAS")
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df = df.drop(columns=["Wt3_sTSAS"])
        with self.assertRaisesRegex(KeyError, "Unable to find weights for Grp3_sTSAS"):
            to_summary(df, scalar_cols=scalar_names, wt_cols=wt_names, start_depth=1)

    def test_gen_summary_dataframe_missing_wt_cols(self):
        """Tests summary dataframe generator raises an exception if start_depth is invalid"""
        scalar_names = list_scalar_names("sTSAS", "group")
        wt_names = list_scalar_weights("sTSAS")[:2]
        df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        with self.assertRaisesRegex(
            ValueError, "Number of weight columns does not match number of scalars"
        ):
            to_summary(df, scalar_cols=scalar_names, wt_cols=wt_names, start_depth=1)

    def test_to_summary_min_item_wt(self):
        """Tests summary dataframe function returns classes with a min weight"""
        scalar_names = list_scalar_names("sTSAS", "group")
        wt_names = list_scalar_weights("sTSAS")
        src_df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        
        # Manually zero out weights below 0.5 and create summary
        df1 = src_df.copy()
        for wt in [1,2,3]:
            df1.loc[df1[f"Wt{wt}_sTSAS"] < 0.5, f"Wt{wt}_sTSAS"] = 0.0

        df1_out= to_summary(
            df1,
            scalar_cols=scalar_names,
            wt_cols=wt_names,
            percent=False,
            resolution=None,
        )

        # Create summary with min_item_wt = 0.5
        df2_out = to_summary(
            src_df,
            scalar_cols=scalar_names,
            percent=False,
            wt_cols=wt_names,
            min_item_wt=0.5,
            resolution=None,
        )

        # Compare the two summaries and check they're the same
        self.assertEqual(df1_out.compare(df2_out).shape, (0, 0))

    def test_to_summary_min_item_pct(self):
        """Tests summary dataframe function returns classes with a min percentage"""
        scalar_names = list_scalar_names("sTSAS", "group")
        wt_names = list_scalar_weights("sTSAS")
        src_df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df_all = to_summary(
            src_df,
            scalar_cols=scalar_names,
            wt_cols=wt_names,
            percent=True,
            resolution=None,
        )

        # Count # of values > 50%
        scalar_cols = list(df_all.columns[3:])
        df_comparator = df_all[scalar_cols] >= 50

        # Create summary with min_item_pct = 50%
        df = to_summary(
            src_df,
            scalar_cols=scalar_names,
            percent=True,
            wt_cols=wt_names,
            min_item_pct=50.0,
            resolution=None,
        )

        # Count values > zero and compare with first count
        df_output = df[scalar_cols] > 0
        self.assertEqual(
            df_output[scalar_cols].compare(df_comparator).shape,
            (0, 0),
        )


    def test_to_summary_max_item_pct(self):
        """Tests summary dataframe function returns classes with a max percentage"""
        scalar_names = list_scalar_names("sTSAS", "group")
        wt_names = list_scalar_weights("sTSAS")
        src_df = pd.read_csv(
            StringIO(setup_scalar_data("scalardata-groups").decode("utf-8"))
        )
        df_all = to_summary(
            src_df,
            scalar_cols=scalar_names,
            wt_cols=wt_names,
            percent=True,
            resolution=None,
        )

        # Count # of values <= 50%
        scalar_cols = list(df_all.columns[2:])
        df_comparator = (df_all[scalar_cols] > 0) & (df_all[scalar_cols] <= 50)

        # Create summary with min_item_pct = 50%
        df = to_summary(
            src_df,
            scalar_cols=scalar_names,
            percent=True,
            wt_cols=wt_names,
            max_item_pct=50.0,
            resolution=None,
        )

        # Count values > zero and compare with first count
        df_output = df[scalar_cols] > 0
        print(f"{df_comparator=}")
        print(f"{df_output=}")

        print(f"{df_all.iloc[0]=}")
        print(f"{df.iloc[0]=}")
        self.assertEqual(
            df_output[scalar_cols].compare(df_comparator).shape,
            (0, 0),
        )
