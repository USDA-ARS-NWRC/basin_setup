#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_basin_setup
----------------------------------

Tests for `basin_setup.basin_setup` module.
"""

import os
import shutil
import unittest
from os.path import abspath, join
from subprocess import check_output

from basin_setup.basin_setup import *
from .basin_setup_test_case import BSTestCase


class TestBasinSetupCLI(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.gfname = 'topo.nc'
        self.cfname = join('output', self.gfname)
        super().setUpClass()

        self.dem = join(self.data_path, 'dem_epsg_32611_100m.tif')
        self.shp = join(self.gold_path, 'basin_outline.shp')

        self.cmd = ('basin_setup -dm {} -f {} -o {} --cell_size 150'
                   ''.format(self.dem,self.shp, self.output))

    def test_ensemble(self):
        """
        Test the full run of the basin_setup command
        """

        shp = abspath(join(self.test_data, "rme_outline.shp"))
        dem = abspath(join(self.test_data, "rme_utm11_wgs84.tif"))

        cmd = "basin_setup -f {} -dm {}".format(shp, dem)
        print("Executing {}".format(cmd))
        check_output(cmd, shell=True)

    def test_parse_extent(self):
        """
        Tests our parse extent function
        """
        parseable_files = \
            {"rme_utm11_wgs84.tif": [519388.498, 4767766.522, 520548.71, 4768818.807],
             "rme_outline.shp": [519582.037277, 4767817.082173, 520402.037277, 4768727.082173]}

        for fname, expected in parseable_files.items():

            extent = parse_extent(join(self.test_data, fname))
            assert extent == expected


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
