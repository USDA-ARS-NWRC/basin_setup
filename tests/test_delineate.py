#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import unittest
from subprocess import check_output
from basin_setup.basin_setup import *
from .basin_setup_test_case import BSTestCase


class TestDelineateCLI(BSTestCase):

    @classmethod
    def setUpClass(self):
        self.gfname = 'basin_outline.shp'
        self.cfname = join('output', self.gfname)
        super().setUpClass()

        self.pour_points = join(self.data_path, 'pour_points.bna')
        self.dem = join(self.data_path, 'dem_epsg_32611_100m.tif')
        self.cmd_str = 'delineate -d {} -p {}  -o {}'.format(
                                                    self.dem,
                                                    self.pour_points,
                                                    self.output
        )

    def test_ensemble(self):
        """
        Test the full run of the basin_setup command
        """
        cmd = self.cmd_str + ' -t 1000'
        self.run_test(self.cmd_str)


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
