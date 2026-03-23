#!/usr/bin/env python3
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
try:
    from helpers import setup_reader, setup_scalar_data
except ImportError:
    from .helpers import setup_reader, setup_scalar_data

from nvcl_kit.constants import Scalar

from nvcl_kit.generators import gen_core_images, gen_downhole_scalar_plots, gen_scalar_by_depth, gen_summary_dataframe, gen_tray_thumb_imgs, list_scalar_names

'''
Test nvcl_kit generator functions
'''
class TestGenerators(unittest.TestCase):

    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid8']),
                                                  get_datasetid_list=MagicMock(return_value=['dsid4']),
                                                  get_tray_thumb_imglogs=MagicMock(return_value=[SimpleNamespace(log_id=70)]),
                                                  get_tray_thumb_jpg=MagicMock(return_value=b'jpg55'),
                                                  get_tray_depths=MagicMock(return_value=[99.0]) )

    def test_gen_tray_thumb_imgs(self):
        '''Tests tray thumbnail generator
        '''
        rdr = setup_reader()
        for n_id, dsid, ilog, depth_list, jpg in gen_tray_thumb_imgs(rdr):
            self.assertEqual(n_id, 'nid8')
            self.assertEqual(dsid, 'dsid4')
            self.assertEqual(ilog.log_id, 70)
            self.assertEqual(depth_list, [99.0])
            self.assertEqual(jpg, b'jpg55')

 
    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid1']),
                                                  get_logs_data=MagicMock(return_value=[SimpleNamespace(log_name='X', log_id=6)]),
                                                  get_borehole_data=MagicMock(return_value='bhd3') )
    def test_gen_scalar_by_depth(self):
        ''' Tests scalar by depth generator
        '''
        rdr = setup_reader()
        for n_id, ild, scalar_data in gen_scalar_by_depth(rdr):
            self.assertEqual(n_id, 'nid1')
            self.assertEqual(ild.log_id, 6)
            self.assertEqual(scalar_data, 'bhd3')


    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid1']),
                                                  get_logs_data=MagicMock(return_value=[]),
                                                  get_borehole_data=MagicMock(return_value='bhd3') )
    def test_gen_scalar_by_depth_no_nid_params(self):
        ''' Tests scalar by depth generator, nvcl id cannot be found
        '''
        rdr = setup_reader()
        into_loop = False
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, nvcl_id_list=['nid2']):
            into_loop = True
        self.assertFalse(into_loop)


    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid1']),
                                                  get_logs_data=MagicMock(return_value=[SimpleNamespace(log_name='X', log_id=6)]),
                                                  get_borehole_data=MagicMock(return_value='bhd3') )
    def test_gen_scalar_by_depth_nid_params(self):
        ''' Tests scalar by depth generator, nvcl id can be found
        '''
        rdr = setup_reader()
        into_loop = False
        for n_id, ild, scalar_data in gen_scalar_by_depth(rdr, nvcl_id_list=['nid1']):
            into_loop = True
        self.assertTrue(into_loop)


    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid1','nid2']),
                                                  get_logs_data=MagicMock(return_value=[
                                                        SimpleNamespace(log_name='X1', log_id=6, log_type='1'),
                                                        SimpleNamespace(log_name='X2', log_id=7, log_type='2'),
                                                        SimpleNamespace(log_name='X3', log_id=8, log_type='3')]),
                                                  get_borehole_data=MagicMock(return_value='bhd3') )
    def test_gen_scalar_by_depth_tid_params(self):
        ''' Tests scalar by depth generator, type id can be found
        '''
        rdr = setup_reader()
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, log_type='1'):
            self.assertEqual(ld.log_type, '1')
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, log_type='2'):
            self.assertEqual(ld.log_type, '2')
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, log_type='3'):
            self.assertEqual(ld.log_type, '3')


    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid1','nid2']),
                                                  get_logs_data=MagicMock(return_value=[
                                                      SimpleNamespace(log_name='Grp1_sTSAT', log_id=6, log_type='1'),
                                                      SimpleNamespace(log_name='Grp2_sTSAT', log_id=7, log_type='2'),
                                                      SimpleNamespace(log_name='Grp3_sTSAT', log_id=8, log_type='3')]),
                                                  get_borehole_data=MagicMock(return_value='bhd3') )
    def test_gen_scalar_by_depth_sc_params(self):
        ''' Tests scalar by depth generator, test looking for scalar classes
        '''
        rdr = setup_reader()
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, scalar_class=Scalar.Grp1_sTSAT):
            self.assertEqual(ld.log_name, 'Grp1_sTSAT')
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, scalar_class=Scalar.Grp2_sTSAT):
            self.assertEqual(ld.log_type, 'Grp2_sTSAT')
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, scalar_class=Scalar.Grp3_sTSAT):
            self.assertEqual(ld.log_type, 'Grp3_sTSAT')
        # Check if all scalars are retrieved when Scalar.ANY is supplied
        cnt = 0
        for n_id, ld, scalar_data in gen_scalar_by_depth(rdr, scalar_class=Scalar.ANY):
            cnt += 1
        self.assertEqual(cnt, 6)


    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid3']),
                                                  get_datasetid_list=MagicMock(return_value=['dsid6']),
                                                  get_scalar_logs=MagicMock(return_value=[SimpleNamespace(log_id=8)]),
                                                  plot_scalar_png=MagicMock(return_value='png9') )
    def test_gen_downhole_scalar_plots(self):
        ''' Tests downhole scalar plot generator
        '''
        rdr = setup_reader()
        for n_id, dsid, scalar_log, png in gen_downhole_scalar_plots(rdr):
            self.assertEqual(n_id, 'nid3')
            self.assertEqual(dsid, 'dsid6')
            self.assertEqual(scalar_log.log_id, 8)
            self.assertEqual(png, 'png9')

    
    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid4']),
                                                  get_datasetid_list=MagicMock(return_value=['dsid0']),
                                                  get_imagery_imglogs=MagicMock(return_value=[SimpleNamespace(log_id=1)]),
                                                  get_mosaic_image=MagicMock(return_value='htm5'),
                                                  get_tray_depths=MagicMock(return_value=[78.0]) )
    def test_gen_core_images(self):
        """Tests core image generator"""
        rdr = setup_reader()
        for n_id, dsid, ilog, depth_list, html in gen_core_images(rdr):
            self.assertEqual(n_id, "nid4")
            self.assertEqual(dsid, "dsid0")
            self.assertEqual(ilog.log_id, 1)
            self.assertEqual(depth_list, [78.0])
            self.assertEqual(html, "htm5")

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Grp1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(return_value=""),
    )
    def test_gen_summary_dataframe_download_error(self):
        """Tests summary dataframe generator handles failed scalar downloads"""
        rdr = setup_reader()
        with self.assertRaisesRegex(
            RuntimeError, "Request to download scalar data failed!"
        ):
            next(gen_summary_dataframe(rdr))

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Grp1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(return_value=""),
    )
    def test_gen_summary_dataframe_continue_on_error_single(self):
        """Tests summary dataframe generator continues on failed scalar downloads (single hole)"""
        rdr = setup_reader()

        df_list = list(gen_summary_dataframe(rdr, continue_on_error=True))
        self.assertTrue(len(df_list) == 0)

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1", "nid2"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Grp1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(side_effect=["", setup_scalar_data("scalardata-groups")]),
    )
    def test_gen_summary_dataframe_continue_on_error_multi(self):
        """Tests summary dataframe generator continues on failed scalar downloads (multi hole)"""
        rdr = setup_reader()

        df_list = list(gen_summary_dataframe(rdr, continue_on_error=True))
        self.assertTrue(len(df_list) == 1)
        meta, df = df_list[0]
        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(df, pd.DataFrame))

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=[]),
        get_logs_data=MagicMock(return_value=[SimpleNamespace(log_name="X", log_id=6)]),
        get_scalar_data=MagicMock(return_value=""),
    )
    def test_gen_summary_dataframe_no_ids(self):
        """Tests summary dataframe generator throws an exception when no NVCL ids are set"""
        rdr = setup_reader()
        with self.assertRaises(RuntimeError):
            next(gen_summary_dataframe(rdr))

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Grp1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(return_value=setup_scalar_data("scalardata-groups")),
    )
    def test_gen_summary_dataframe_grp(self):
        """Tests summary dataframe generator returns group scalars"""
        rdr = setup_reader()

        _, df = next(gen_summary_dataframe(rdr, scalar_level="group", scalar_set="sTSAS"))
        self.assertCountEqual(
            list(df.columns),
            [
                "BoreholeID",
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
        self.assertTrue(np.all(df["BoreholeID"]=="nid1"))

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Min1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Min2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Min3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(
            return_value=setup_scalar_data("scalardata-minerals")
        ),
    )
    def test_gen_summary_dataframe_min(self):
        """Tests summary dataframe generator returns mineral scalars"""
        rdr = setup_reader()

        _, df = next(gen_summary_dataframe(rdr, scalar_level="min", scalar_set="sTSAS"))
        self.assertCountEqual(
            list(df.columns),
            [
                "BoreholeID",
                "StartDepth",
                "EndDepth",
                "Alunite-K",
                "Alunite-NH",
                "Alunite-Na",
                "Ankerite",
                "Aspectral",
                "Biotite",
                "Calcite",
                "Chlorite-Fe",
                "Chlorite-FeMg",
                "Chlorite-Mg",
                "Diaspore",
                "Dickite",
                "Dolomite",
                "Epidote",
                "Gibbsite",
                "Gypsum",
                "Jarosite",
                "Kaolinite-PX",
                "Kaolinite-WX",
                "Magnesite",
                "Montmorillonite",
                "Muscovite",
                "MuscoviticIllite",
                "Nacrite",
                "Paragonite",
                "ParagoniticIllite",
                "Phengite",
                "PhengiticIllite",
                "Phlogopite",
                "Prehnite",
                "Pyrophyllite",
                "Riebeckite",
                "Rubellite",
                "Saponite",
                "Siderite",
                "Tourmaline",
                "Tourmaline-Fe",
                "WhiteMarker",
                "Wood",
                "Zoisite",
            ],
        )
        self.assertTrue(np.all(df["BoreholeID"] == "nid1"))

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1", "nid2"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Grp1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(return_value=setup_scalar_data("scalardata-groups")),
    )
    def test_gen_summary_dataframe_multi_hole(self):
        """Tests summary dataframe generator returns group scalars for multiple boreholes"""
        rdr = setup_reader()

        for i, (_, df) in enumerate(gen_summary_dataframe(rdr, scalar_level="group", scalar_set="sTSAS"), 1):
            self.assertCountEqual(
                list(df.columns),
                [
                    "BoreholeID",
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
            self.assertTrue(np.all(df["BoreholeID"]==f"nid{i}"))
        # Check we only return two dataframes
        self.assertEqual(i, 2)

    @patch.multiple(
        "nvcl_kit.reader.NVCLReader",
        get_nvcl_id_list=MagicMock(return_value=["nid1", "nid2"]),
        get_logs_data=MagicMock(return_value=[
                                SimpleNamespace(log_name='Grp1 sTSAS', log_id=6, log_type='1', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp2 sTSAS', log_id=7, log_type='2', algorithm_id='109'),
                                SimpleNamespace(log_name='Grp3 sTSAS', log_id=8, log_type='3', algorithm_id='109')]),
        get_scalar_data=MagicMock(return_value=setup_scalar_data("scalardata-groups")),
    )
    def test_gen_summary_dataframe_concat(self):
        """Tests summary dataframe generator returns group scalars for multiple boreholes"""
        rdr = setup_reader()

        for i, (_, df) in enumerate(gen_summary_dataframe(rdr, scalar_level="group", scalar_set="sTSAS", concat_data=True), 1):
            self.assertCountEqual(
                list(df.columns),
                [
                    "BoreholeID",
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
            
            self.assertEqual(["nid1", "nid2"], df["BoreholeID"].unique().tolist())
        # Check we only return one dataframe (containing both holes)
        self.assertEqual(i, 1)

    def test_list_scalar_names_grp(self):
        """Tests list_scalar_names() function for group level scalars"""
        scalars = list_scalar_names(scalar_set="uTSAS", scalar_level="group")
        self.assertEqual(scalars, ["Grp1 uTSAS", "Grp2 uTSAS", "Grp3 uTSAS"])

        scalars = list_scalar_names(scalar_set="uTSAS", scalar_level="grp")
        self.assertEqual(scalars, ["Grp1 uTSAS", "Grp2 uTSAS", "Grp3 uTSAS"])

    def test_list_scalar_names_min(self):
        """Tests list_scalar_names() function for mineral level scalars"""
        scalars = list_scalar_names(scalar_set="uTSAS", scalar_level="mineral")
        self.assertEqual(scalars, ["Min1 uTSAS", "Min2 uTSAS", "Min3 uTSAS"])

        scalars = list_scalar_names(scalar_set="uTSAS", scalar_level="min")
        self.assertEqual(scalars, ["Min1 uTSAS", "Min2 uTSAS", "Min3 uTSAS"])

    def test_list_scalar_names_error(self):
        """Tests list_scalar_names() function with invalid scalar level"""
        with self.assertRaisesRegex(ValueError, "Scalar level must be 'Group', or 'Mineral'."):
            list_scalar_names(scalar_set="uTSAS", scalar_level="invalid")
