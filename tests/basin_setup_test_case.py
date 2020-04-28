#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from subprocess import check_output
from os.path import abspath, join, dirname, isdir
from netCDF4 import Dataset
import numpy as np
import shutil

class BSTestCase(unittest.TestCase):

        # Assign self.gold and self.compare netcdf datasets in setup
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.test_path = abspath(dirname(__file__))
        self.data_path = join(self.test_path, 'data')
        self.gold_path = join(self.data_path, 'gold')
        self.output = join(self.data_path, dirname(self.cfname))

        if isdir(self.output):
            shutil.rmtree(self.output)

    def close(self):
        self.gold.close()
        self.compare.close()

    def open(self):
        '''
        Open the netcdfs
        '''
        self.gold = Dataset( join(self.gold_path, self.gfname))
        self.compare = Dataset(join(self.data_path, self.cfname))

    def run_test(self, cmd):
        print("Running: {}".format(cmd))
        check_output(cmd, shell=True)
        self.open()
        self.assert_nan_count_same()
        self.assert_all_images_equal()
        self.close()
        shutil.rmtree(self.output)

    def assert_nan_count_same(self):
        '''
        Insure were are using our NaNs the same as before by counting them
        and returng true if they are the same

        Args:
            vcompare: Numpy array of the compare datatset
            vgold: Numpy array of the gold dataset

        '''
        for v in self.gold.variables.keys():
            compare_nan = np.count_nonzero(np.isnan(self.compare.variables[v][:]))
            gold_nan = np.count_nonzero(np.isnan(self.gold.variables[v][:]))
            self.assertTrue(compare_nan == gold_nan)


    def assert_all_images_equal(self, decimal=8):
        '''
        Insure were are using our NaNs the same as before by counting them
        and returng true if they are the same

        Args:
            decimal: Number of decimals to worry about with comparison
        '''

        for v in self.gold.variables.keys():
            if v not in ['projection']:
                np.testing.assert_almost_equal(self.compare.variables[v][:],
                                                self.gold.variables[v][:],
                                                decimal=decimal)
