import logging
import os
import shutil
import unittest
from copy import deepcopy
from pathlib import Path

import netCDF4 as nc
import numpy as np
from inicheck.tools import get_user_config

import basin_setup


class BasinSetupLakes(unittest.TestCase):

    BASE_INI_FILE_NAME = 'config.ini'
    CRS = 'epsg:32611'

    test_dir = Path(basin_setup.__file__).parent.parent.joinpath('tests')
    basin_dir = test_dir.joinpath('Lakes')
    gold_dir = test_dir.joinpath(basin_dir, 'gold')
    config_file = os.path.join(basin_dir, BASE_INI_FILE_NAME)

    @classmethod
    def base_config_copy(cls):
        return deepcopy(cls._base_config)

    @classmethod
    def load_base_config(cls):
        cls._base_config = get_user_config(
            cls.config_file, modules='basin_setup')

    @classmethod
    def setUpClass(cls):
        cls.load_base_config()
        cls.create_output_dir()

    @classmethod
    def tearDownClass(cls):
        cls.remove_output_dir()

    def tearDown(self):
        logging.shutdown()

    @classmethod
    def create_output_dir(cls):
        folder = os.path.join(
            cls._base_config.cfg['generate_topo']['output_folder'])

        # Remove any potential files to ensure fresh run
        if os.path.isdir(folder):
            shutil.rmtree(folder)

        os.makedirs(folder)
        cls.output_dir = Path(folder)

    @classmethod
    def remove_output_dir(cls):
        if hasattr(cls, 'output_dir') and \
                os.path.exists(cls.output_dir):
            shutil.rmtree(cls.output_dir)

    @staticmethod
    def assert_gold_equal(gold, not_gold, error_msg):
        """Compare two arrays
        Arguments:
            gold {array} -- gold array
            not_gold {array} -- not gold array
            error_msg {str} -- error message to display
        """

        if os.getenv('NOT_ON_GOLD_HOST') is None:
            try:
                np.testing.assert_array_equal(
                    not_gold,
                    gold,
                    err_msg=error_msg
                )
            except AssertionError:
                for rtol in [1e-5, 1e-4]:
                    status = np.allclose(
                        not_gold,
                        gold,
                        atol=0,
                        rtol=rtol
                    )
                    if status:
                        break
                if not status:
                    raise AssertionError(error_msg)
                print('Arrays are not exact match but close with rtol={}'.format(rtol))  # noqa
        else:
            np.testing.assert_almost_equal(
                not_gold,
                gold,
                decimal=3,
                err_msg=error_msg
            )

    def compare_netcdf_files(self, gold_file, output_file):
        """
        Compare two netcdf files to ensure that they are identical. The
        tests will compare the attributes of each variable and ensure that
        the values are exact
        """

        gold = nc.Dataset(self.gold_dir.joinpath(gold_file))
        test = nc.Dataset(self.output_dir.joinpath(output_file))

        # go through all variables and compare everything including
        # the attributes and data
        for var_name, v in gold.variables.items():

            # compare the dimensions
            for att in gold.variables[var_name].ncattrs():
                if att == '_FillValue':
                    self.assertTrue(
                        np.isnan(getattr(test.variables[var_name], att)))
                else:
                    self.assertEqual(
                        getattr(gold.variables[var_name], att),
                        getattr(test.variables[var_name], att))

            # only compare those that are floats
            if gold.variables[var_name].datatype != np.dtype('S1'):
                error_msg = "Variable: {0} did not match gold standard". \
                    format(var_name)
                self.assert_gold_equal(
                    gold.variables[var_name][:],
                    test.variables[var_name][:],
                    error_msg
                )

        gold.close()
        test.close()
