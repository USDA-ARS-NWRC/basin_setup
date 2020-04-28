from basin_setup.grm import *
import unittest
import pandas as pd
from subprocess import check_output
from os.path import abspath, join, dirname, isdir
from netCDF4 import Dataset
import numpy as np



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

    @classmethod
    def tearDown(self):
        super().setUpClass()
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

    def run_test(self):
        self.open()
        self.assert_nan_count_same()
        self.assert_all_images_equal()
        self.close()

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

class TestGRM(BSTestCase):

    @classmethod
    def setUpClass(self):
        self.gfname = 'lidar_depths_wy2019.nc'
        self.cfname = join('output', self.gfname)
        super().setUpClass()


    def test_lidar_images(self):
        '''
        run GRM with no special flags with one file
        '''
        # Add both images at once
        image = join(self.data_path, 'USCALB*_test_100m.tif')
        topo = join(self.gold_path, 'topo.nc')
        cmd = 'grm -i {} -t {} -b lakes --o {}'.format(image, topo, self.output)
        print("Running: {}".format(cmd))
        check_output(cmd, shell=True)
        self.run_test()

# class TestGRM(BSTestCase):
#
#     def test_parse_fname_date(self):
#         """
#         Test the parsing of dates
#         """
#
#         parseable = ['20200414.tif',
#                      'ASO_SanJoaquin_20200414_SUPERsnow_depth_50p0m_agg.tif',
#                      'USCATE20200414_ARS_MERGED_depth_50p0m_agg.tif']
#
#         not_parseable = ['ASO_SanJoaquin_2020Apr14_SUPERsnow_depth_50p0m_agg.tif',
#                          'ASO_SanJoaquin_20205030_SUPERsnow_depth_50p0m_agg.tif',
#                          '04142020.tif']
#         true_dt = pd.to_datetime('2020-04-14')
#
#         for p in parseable:
#             dt = parse_fname_date(p)
#             assert dt == true_dt
#
#         for p in not_parseable:
#             dt = parse_fname_date(p)
#             assert dt is None
