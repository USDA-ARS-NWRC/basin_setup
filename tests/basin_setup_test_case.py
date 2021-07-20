#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
import unittest
from os.path import abspath, dirname, isdir, join
from subprocess import check_output

import geopandas as gpd
import numpy as np
import pandas as pd
from netCDF4 import Dataset


class FunctionalRunCase(unittest.TestCase):
    '''
    Test case just designed to simply run the test command
    '''
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.test_path = abspath(dirname(__file__))
        self.basin_path = join(self.test_path, 'Lakes')
        self.data_path = join(self.basin_path, 'data')
        self.gold_path = join(self.basin_path, 'gold')

    def run_cmd(self, cmd):
        # print("Running: {}".format(cmd))
        s = check_output(cmd, shell=True)
        return s.decode('utf-8')


class BSTestCase(FunctionalRunCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.output = join(self.basin_path, 'output')

        if isdir(self.output):
            shutil.rmtree(self.output)

    def close(self):
        if self.ext == 'nc':
            self.gold.close()
            self.compare.close()

    def open(self):
        '''
        Open the netcdfs datsets and shapefiles (as geopandas)
        '''
        self.ext = self.gfname.split('.')[-1]

        gf = join(self.gold_path, self.gfname)
        cf = join(join(self.output, self.cfname))

        # Netcdf comparison, retrieve the dataset
        if self.ext == 'nc':
            self.gold = Dataset(gf)
            self.compare = Dataset(cf)

        # Shapefile comparison, open using geopandas and make dataframes
        elif self.ext == 'shp':
            self.gold = gpd.read_file(gf)
            self.compare = gpd.read_file(cf)

        else:
            raise Exception(
                "File with ext == {} not implemented".format(
                    self.ext))

    def run_test(self, cmd):
        '''
        Run the test and evaluate the data
        '''
        self.run_cmd(cmd)
        self.open()
        self.assert_nan_count_same()
        self.assert_gis_equal()
        self.close()
        shutil.rmtree(self.output)

    def assert_nan_count_same(self):
        '''
        Insure were are using our NaNs the same as before by counting them
        and returng true if they are the same
        '''

        if self.ext == 'nc':
            for v in self.gold.variables.keys():
                compare_nan = np.count_nonzero(
                    np.isnan(self.compare.variables[v][:]))
                gold_nan = np.count_nonzero(
                    np.isnan(self.gold.variables[v][:]))
                self.assertTrue(compare_nan == gold_nan)

        elif self.ext == 'shp':
            pass

    def assert_gis_equal(self, decimal=8):
        '''
        Insure were are using our NaNs the same as before by counting them
        and returng true if they are the same

        Args:
            decimal: Number of decimals to worry about with comparison
        '''

        if self.ext == 'nc':
            for v in self.gold.variables.keys():
                if v not in ['projection']:
                    np.testing.assert_almost_equal(
                        self.compare.variables[v][:],
                        self.gold.variables[v][:],
                        decimal=decimal)
        elif self.ext == 'shp':
            pd.testing.assert_frame_equal(self.compare, self.gold)
