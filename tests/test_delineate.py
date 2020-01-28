#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_basin_setup
----------------------------------

Tests for `basin_setup.basin_setup` module.
"""

import unittest
from basin_setup.basin_setup import *
import shutil
import os
from subprocess import check_output

class TestDelineate(unittest.TestCase):

    def test_ensemble(self):
        """
        Test the full run of the basin_setup command
        """
        cmd = "delineate -f RME/rme_outline.shp -dm RME/rme_utm11_wgs84.tif"
        print("Executing {}".format(cmd))
        check_output(cmd, shell=True)


    # def test_parse_extent(self):
    #     """
    #     Tests our parse extent function
    #     """
    #     parseable_files = {"tif":"rme_utm11_wgs_84.tif","shp":"rme_outline.shp"}
    #
    #     for k,v
    #     extent = parse_extent(fname, cellsize_return=False, x_field='x', y_field='y'):


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
