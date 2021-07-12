import os

from basin_setup.utils.parse_extent import parse_extent

from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestParseExtents(BasinSetupLakes):

    def test_tif(self):

        file_name = os.path.join(
            self.basin_dir, 'data', 'dem_epsg_32611_100m.tif')
        extents, cellsize = parse_extent(file_name)

        self.assertListEqual(
            extents,
            [318520.405, 4157537.075, 329820.405, 4167937.075]
        )
        self.assertTrue(cellsize == 100)

    def test_netcdf(self):
        file_name = os.path.join(
            self.basin_dir, 'gold', 'topo.nc')
        extents, cellsize = parse_extent(file_name)

        self.assertListEqual(
            extents,
            [319570.40625, 4157787.0, 328270.40625, 4167087.0]
        )
        self.assertListEqual(cellsize, [150, 150])

    def test_shapefile(self):
        file_name = os.path.join(
            self.basin_dir, 'gold', 'basin_outline.shp')
        extents, cellsize = parse_extent(file_name)

        self.assertListEqual(
            extents,
            [320320.405027, 4158537.07547, 327520.405027, 4166337.07547]
        )
        self.assertIsNone(cellsize)
