#!/usr/bin/env python3
import sys, os
import unittest

from types import SimpleNamespace

from unittest.mock import patch, MagicMock

from nvcl_kit.generators import gen_tray_thumb_imgs, gen_scalar_by_depth
from nvcl_kit.generators import gen_downhole_scalar_plots, gen_core_images
from nvcl_kit.constants import Scalar

from helpers import setup_reader

'''
Test nvcl_kit generator functions
'''
class TestGenerators(unittest.TestCase):

    @patch.multiple('nvcl_kit.reader.NVCLReader', get_nvcl_id_list=MagicMock(return_value=['nid8']),
                                                  get_datasetid_list=MagicMock(return_value=['dsid4']),
                                                  get_tray_thumb_imglogs=MagicMock(return_value=[SimpleNamespace(log_id=70)]),
                                                  get_tray_thumb_jpg=MagicMock(return_value='jpg55'),
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
            self.assertEqual(jpg, 'jpg55')

 
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
        ''' Tests core image generator
        '''
        rdr = setup_reader()
        for n_id, dsid, ilog, depth_list, html in gen_core_images(rdr):
            self.assertEqual(n_id, 'nid4')
            self.assertEqual(dsid, 'dsid0')
            self.assertEqual(ilog.log_id, 1)
            self.assertEqual(depth_list, [78.0])
            self.assertEqual(html, 'htm5')
