#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from os.path import join
from subprocess import check_output

import numpy as np
import pandas as pd

from basin_setup.grm import *

from .basin_setup_test_case import BSTestCase


class TestGRMCLI(BSTestCase):

    @classmethod
    def setUpClass(self):
        self.gfname = 'lidar_depths_wy2019.nc'
        self.cfname = join('output', self.gfname)
        super().setUpClass()

        self.image_1 = join(self.data_path, 'USCALB20190325_test_100m.tif')
        self.image_2 = join(self.data_path, 'USCALB20190501_test_100m.tif')
        self.topo = join(self.gold_path, 'topo.nc')
        self.cmd_str = 'grm -i {} -t {} -b lakes -o {}'

    def test_lidar_images(self):
        '''
        run GRM with no special flags with 2 lidar flights
        '''

        # Add both images at once
        cmd = self.cmd_str.format(" ".join([self.image_1, self.image_2]),
                                  self.topo,
                                  self.output)
        self.run_test(cmd)

    def test_appending_lidar_images(self):
        '''
        run GRM with no special flags with 2 lidar flights added separately
        '''

        # Add 1 image and run without testing
        cmd = self.cmd_str.format(self.image_1, self.topo, self.output)
        check_output(cmd, shell=True)

        # Append the next and test
        cmd = self.cmd_str.format(self.image_2, self.topo, self.output)
        self.run_test(cmd)

    def test_manual_dates(self):
        # Add both images at once, use dates shift by a day to check the dates
        # ... in the file
        cmd_str = self.cmd_str + ' -dt {}'
        cmd = cmd_str.format(" ".join([self.image_1, self.image_2]),
                             self.topo,
                             self.output,
                             " ".join(['20190326', '20190502']))

        print(cmd)
        check_output(cmd, shell=True)
        self.open()
        t = self.compare.variables['time'][:] - self.gold.variables['time'][:]
        print(t)
        self.assertTrue(np.all(t == 24))
        self.close()


class TestGRM(unittest.TestCase):
    '''
    Tests for running the test class
    '''

    def test_parse_fname_date(self):
        """
        Test the parsing of dates
        """

        parseable = ['20200414.tif',
                     'ASO_SanJoaquin_20200414_SUPERsnow_depth_50p0m_agg.tif',
                     'USCATE20200414_ARS_MERGED_depth_50p0m_agg.tif']

        not_parseable = ['ASO_SanJoaquin_2020Apr14_SUPERsnow_depth_50p0m_agg.tif',
                         'ASO_SanJoaquin_20205030_SUPERsnow_depth_50p0m_agg.tif',
                         '04142020.tif']
        true_dt = pd.to_datetime('2020-04-14')

        for p in parseable:
            dt = parse_fname_date(p)
            assert dt == true_dt

        for p in not_parseable:
            dt = parse_fname_date(p)
            assert dt is None
