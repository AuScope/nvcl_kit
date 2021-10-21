#!/usr/bin/env python3
import sys, os
import unittest
from unittest.mock import patch, Mock
from requests.exceptions import Timeout, RequestException
import logging

from types import SimpleNamespace

from nvcl_kit.param_builder import param_builder

'''
To run this from the command line to test code in local repo:

$ export PYTHONPATH=$HOME/gitlab/nvcl_kit
$ python -m unittest test_parambuilder.py

or use 'tox' to test the packaged 'pypi' version 

'''
PROVS = ['vic', 'Victoria', 'sa', 'South Australia', 'nsw', 'New South Wales', 'nt',
                     'Northern Territory', 'wa', 'Western Australia', 'tas', 'Tasmania', 'qld',
                     'Queensland']

OPTS = ['bbox', 'polygon', 'borehole_crs', 'wfs_version', 'depths', 'wfs_url', 'nvcl_url',
                   'max_boreholes', 'use_local_filtering']


class TestParamBuilder(unittest.TestCase):


    def test_bad_provider(self):
        """ Test badly spelt provider name
        """
        with self.assertLogs('nvcl_kit.param_builder', level='WARN') as nvcl_log:
            pb = param_builder('qr')
            self.assertIn('Cannot recognise provider parameter', nvcl_log.output[0])
            self.assertIsNone(pb)

    def test_bad_provider_type(self):
        """ Test bad provider name type
        """
        with self.assertLogs('nvcl_kit.param_builder', level='WARN') as nvcl_log:
            pb = param_builder(1.5)
            self.assertIn('Provider parameter must be a string', nvcl_log.output[0])
            self.assertIsNone(pb)

    def test_providers(self):
        """ Test different ways of supplying valid provider names
        """
        for prov in PROVS:
            pb = param_builder(prov)
            self.assertIsNotNone(pb)
            pb = param_builder(prov.upper())
            self.assertIsNotNone(pb)
            pb = param_builder(prov.lower())
            self.assertIsNotNone(pb)

    def test_bad_option(self):
        """ Test a bad option name
        """
        with self.assertLogs('nvcl_kit.param_builder', level='WARN') as nvcl_log:
            pb = param_builder('nt', blah=1.0)
            self.assertIn('blah is not a valid param_builder option', nvcl_log.output[0])
            self.assertIsNone(pb)

    def test_options(self):
        """ Test that options are set in returned structure
        """
        for opt in OPTS:
            d = { opt: 1.0 }
            pb = param_builder('vic', **d)
            self.assertIsNotNone(pb)
            self.assertEqual(getattr(pb, opt.upper()), 1.0)
