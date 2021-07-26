import os

from basin_setup.utils import domain_extent
from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestParseFromFile(BasinSetupLakes):

    def test_tif(self):

        file_name = os.path.join(
            self.basin_dir, 'data', 'dem_epsg_32611_100m.tif')
        extents, cellsize = domain_extent.parse_from_file(file_name)

        self.assertListEqual(
            extents,
            [318520.405, 4157537.075, 329820.405, 4167937.075]
        )
        self.assertTrue(cellsize == 100)

    def test_netcdf(self):
        file_name = os.path.join(
            self.basin_dir, 'gold', 'landfire_140', 'topo.nc')
        extents, cellsize = domain_extent.parse_from_file(file_name)

        self.assertListEqual(
            extents,
            [319570.40625, 4157787.0, 328270.40625, 4167087.0]
        )
        self.assertListEqual(cellsize, [150, 150])

    def test_shapefile(self):
        file_name = os.path.join(
            self.basin_dir, 'gold', 'basin_outline.shp')
        extents, cellsize = domain_extent.parse_from_file(file_name)

        self.assertListEqual(
            extents,
            [320320.405027, 4158537.07547, 327520.405027, 4166337.07547]
        )
        self.assertIsNone(cellsize)


class TestConditionToCellsize(BasinSetupLakes):

    def test_no_change(self):
        extent = [320320, 4158537, 327520, 4166337]
        extents = domain_extent.condition_to_cellsize(extent, cell_size=50)
        self.assertListEqual(extent, extents)

    def test_right_left(self):
        extent = [320318, 4158537, 327520, 4166337]
        extents = domain_extent.condition_to_cellsize(extent, cell_size=50)
        self.assertListEqual(
            extents,
            [320294.0, 4158537.0, 327544.0, 4166337.0]
        )

    def test_top_bottom(self):
        extent = [320320, 4158530, 327520, 4166337]
        extents = domain_extent.condition_to_cellsize(extent, cell_size=50)
        self.assertListEqual(
            extents,
            [320320.0, 4158508.5, 327520.0, 4166358.5]
        )

    def test_both(self):
        extent = [320318, 4158530, 327520, 4166337]
        extents = domain_extent.condition_to_cellsize(extent, cell_size=50)
        self.assertListEqual(
            extents,
            [320294.0, 4158508.5, 327544.0, 4166358.5]
        )
