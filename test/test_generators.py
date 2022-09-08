#!/usr/bin/env python3
import sys, os
import unittest

from types import SimpleNamespace

from unittest.mock import patch, MagicMock

from nvcl_kit.generators import gen_tray_thumb_imgs, gen_scalar_by_depth
from nvcl_kit.generators import gen_downhole_scalar_plots, gen_core_images

from helpers import setup_reader

'''
To run this from the command line to test code in local repo:

$ export PYTHONPATH=$HOME/gitlab/nvcl_kit
$ python -m unittest test_generators.py

or use 'tox' to test the packaged 'pypi' version 

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
                                                  get_imagelog_data=MagicMock(return_value=[SimpleNamespace(log_name='X', log_id=6)]),
                                                  get_borehole_data=MagicMock(return_value='bhd3') )
    def test_gen_scalar_by_depth(self):
        ''' Tests scalar by depth generator
        '''
        rdr = setup_reader()
        for n_id, ild, scalar_data in gen_scalar_by_depth(rdr):
            self.assertEqual(n_id, 'nid1')
            self.assertEqual(ild.log_id, 6)
            self.assertEqual(scalar_data, 'bhd3')

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