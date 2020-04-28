#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from subprocess import check_output
from os.path import abspath, join, dirname, isdir
from netCDF4 import Dataset
import numpy as np
import shutil
import geopandas as gpd
import pandas as pd

class BSTestCase(unittest.TestCase):

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
        if self.ext == 'nc':
            self.gold.close()
            self.compare.close()

    def open(self):
        '''
        Open the netcdfs
        '''
        self.ext = self.gfname.split('.')[-1]

        gf =  join(self.gold_path, self.gfname)
        cf =  join(join(self.data_path, self.cfname))
        if self.ext == 'nc':
            self.gold = Dataset(gf)
            self.compare = Dataset(cf)

        elif self.ext == 'shp':
            self.gold = gpd.read_file(gf)
            self.compare = gpd.read_file(cf)

        else:
            raise Exception("File with ext == {} not implemented".format(self.ext))


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
        if self.ext == 'nc':
            for v in self.gold.variables.keys():
                compare_nan = np.count_nonzero(np.isnan(self.compare.variables[v][:]))
                gold_nan = np.count_nonzero(np.isnan(self.gold.variables[v][:]))
                self.assertTrue(compare_nan == gold_nan)

        elif self.ext == 'shp':
            pass

    def assert_all_images_equal(self, decimal=8):
        '''
        Insure were are using our NaNs the same as before by counting them
        and returng true if they are the same

        Args:
            decimal: Number of decimals to worry about with comparison
        '''
        if self.ext == 'nc':
            for v in self.gold.variables.keys():
                if v not in ['projection']:
                    np.testing.assert_almost_equal(self.compare.variables[v][:],
                                                    self.gold.variables[v][:],
                                                    decimal=decimal)
        elif self.ext == 'shp':
            pd.testing.assert_frame_equal(self.compare, self.gold)
