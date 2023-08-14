#!/usr/bin/env python3
import unittest
from nvcl_kit.constants import Scalar, has_tsa, has_cls, has_SWIR, has_TIR, has_VNIR


'''
Tests for the constant module
'''

class TestConstants(unittest.TestCase):

    def test_has_tsa(self):
        ''' Tests 'has_tsa' API
        '''
        self.assertFalse(has_tsa(Scalar.Min1_sjCLST))
        self.assertTrue(has_tsa(Scalar.Bound_Water_dTSAS))
        self.assertFalse(has_tsa('blah'))
        self.assertTrue(has_tsa("Error dTSAS"))
        self.assertFalse(has_tsa("Min1 ujCLST"))

    def test_has_cls(self):
        ''' Tests 'has_cls' API
        '''
        self.assertTrue(has_cls(Scalar.Min1_sjCLST))
        self.assertFalse(has_cls(Scalar.Bound_Water_dTSAS))
        self.assertFalse(has_cls('blah'))
        self.assertFalse(has_cls("Error dTSAS"))
        self.assertTrue(has_cls("Min1 ujCLST"))

    def has_SWIR(self):
        ''' Tests 'has_SWIR' API
        '''
        self.assertFalse(has_SWIR(Scalar.Min1_sjCLST))
        self.assertFalse(has_SWIR("Min1 ujCLST"))
        self.assertTrue(has_SWIR(Scalar.Bound_Water_dTSAS))
        self.assertTrue(has_SWIR("Bound_Water uTSAS"))
        self.assertFalse(has_SWIR('blah'))
        self.assertTrue(has_SWIR(Scalar.Grp1_uTSAS))
        self.assertTrue(has_SWIR("Grp1 uTSAS"))
        self.assertFalse(has_SWIR(Scalar.Grp1_uTSAT))
        self.assertFalse(has_SWIR("Grp1 uTSAT"))
        self.assertFalse(has_SWIR(Scalar.Grp1_uTSAV))
        self.assertFalse(has_SWIR("Grp1 uTSAV"))

    def has_TIR(self):
        ''' Tests 'has_TIR' API
        '''
        self.assertTrue(has_TIR(Scalar.Min1_sjCLST))
        self.assertTrue(has_TIR("Min1 ujCLST"))
        self.assertFalse(has_TIR(Scalar.Bound_Water_dTSAS))
        self.assertFalse(has_TIR("Bound_Water uTSAS"))
        self.assertFalse(has_TIR('blah'))
        self.assertFalse(has_TIR(Scalar.Grp1_uTSAS))
        self.assertFalse(has_TIR("Grp1 uTSAS"))
        self.assertTrue(has_TIR(Scalar.Grp1_uTSAT))
        self.assertTrue(has_TIR("Grp1 uTSAT"))
        self.assertFalse(has_TIR(Scalar.Grp1_uTSAV))
        self.assertFalse(has_TIR("Grp1 uTSAV"))

    def has_VNIR(self):
        ''' Tests 'has_VNIR' API
        '''
        self.assertFalse(has_VNIR(Scalar.Min1_sjCLST))
        self.assertFalse(has_VNIR("Min1 ujCLST"))
        self.assertFalse(has_VNIR(Scalar.Bound_Water_dTSAS))
        self.assertFalse(has_VNIR("Bound_Water uTSAS"))
        self.assertFalse(has_VNIR('blah'))
        self.assertFalse(has_VNIR(Scalar.Grp1_uTSAS))
        self.assertFalse(has_VNIR("Grp1 uTSAS"))
        self.assertFalse(has_VNIR(Scalar.Grp1_uTSAT))
        self.assertFalse(has_VNIR("Grp1 uTSAT"))
        self.assertTrue(has_VNIR(Scalar.Grp1_uTSAV))
        self.assertTrue(has_VNIR("Grp1 uTSAV"))
