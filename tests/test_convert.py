#!/usr/bin/env python
# -*- coding: utf-8 -*-

from basin_setup.grm import *
import unittest
import pandas as pd
from subprocess import check_output
from os.path import join
import numpy as np
from .basin_setup_test_case import FunctionalRunCase
from os.path import join

class TestConvertCLI(FunctionalRunCase):

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.topo = join(self.gold_path, 'topo.nc')
        self.cmd_str = 'nc2shp -f {}'

    def test_nc2shp_no_variables(self):
        '''
        Run the nc2shp command without variables
        '''
        # Attempt to export all the masks
        cmd = self.cmd_str.format(self.topo)
        s = self.run_cmd(cmd)
        assert 'error' not in s.lower()


    def test_nc2shp_w_variables(self):
        '''
        Run the nc2shp command with variables
        '''
        # Attempt to export the basin masks
        cmd = self.cmd_str.format(self.topo)
        s = self.run_cmd(cmd + ' -v mask')
        assert 'error' not in s.lower()

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
