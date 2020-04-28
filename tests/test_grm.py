from basin_setup.grm import *
import unittest
import pandas as pd


class TestGRM(unittest.TestCase):

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
