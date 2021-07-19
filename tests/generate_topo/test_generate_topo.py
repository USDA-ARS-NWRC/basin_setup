import os
from basin_setup.generate_topo.vegetation import Landfire140
from inicheck.config import UserConfig
from rasterio import Affine
import xarray as xr

from basin_setup.generate_topo import GenerateTopo
from basin_setup.generate_topo.shapefile import Shapefile
from basin_setup.utils import domain_extent
from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestBasinSetup(BasinSetupLakes):

    # TODO change extents to this instead of decimals
    # EXTENTS = [318520.0, 4157550.0, 329470.0, 4167900.0]
    EXTENTS = [319570.405027, 4157787.07547, 328270.405027, 4167087.07547]
    EXTENTS_RASTER = [319570.405, 4157787.075, 328270.405, 4167087.075]

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def setUp(self) -> None:
        self.subject = GenerateTopo(config_file=self.config_file)

    def test_init(self):
        self.assertIsInstance(self.subject.ucfg, UserConfig)

    def test_set_extents(self):
        self.subject.set_extents()
        self.assertListEqual(
            self.subject.extents,
            self.EXTENTS
        )
        self.assertIsInstance(self.subject.transform, Affine)
        self.assertTrue(len(self.subject.x) == 58)
        self.assertTrue(len(self.subject.y) == 62)

    def test_load_basin_shapefiles(self):
        self.subject.load_basin_shapefiles()

        self.assertTrue(len(self.subject.basin_shapefiles) == 1)
        self.assertIsInstance(self.subject.basin_shapefiles[0], Shapefile)
        self.assertDictEqual(self.subject.basin_shapefiles[0].crs, self.CRS)

    def test_load_dem(self):
        self.subject.crs = self.CRS
        self.subject.extents = self.EXTENTS
        self.subject.load_dem()

        extents, cell_size = domain_extent.parse_from_file(
            'tests/Lakes/output/temp/clipped_dem.tif')

        self.assertListEqual(extents, self.EXTENTS_RASTER)
        self.assertTrue(cell_size == self.subject.config['cell_size'])
        self.assertIsInstance(self.subject.dem, xr.DataArray)
        self.assertCountEqual(list(self.subject.dem.coords.keys()), [
                              'y', 'x', 'spatial_ref'])

    def test_load_vegetation(self):
        self.subject.crs = self.CRS
        self.subject.extents = self.EXTENTS
        self.subject.load_vegetation()

        extents, cell_size = domain_extent.parse_from_file(
            'tests/Lakes/output/temp/clipped_veg_type.tif')

        self.assertListEqual(extents, self.EXTENTS_RASTER)
        self.assertTrue(cell_size == self.subject.config['cell_size'])
        self.assertIsInstance(self.subject.veg, Landfire140)
        self.assertCountEqual(
            list(self.subject.veg.veg_tau_k.coords.keys()),
            ['y', 'x', 'spatial_ref']
        )
        self.assertCountEqual(
            list(self.subject.veg.veg_height.coords.keys()),
            ['y', 'x', 'spatial_ref']
        )

    def test_run(self):
        gt = GenerateTopo(config_file=self.config_file)
        gt.run()

        ds = xr.open_dataset(os.path.join(self.basin_dir, 'output', 'topo.nc'))

        self.assertCountEqual(
            list(ds.coords.keys()),
            ['y', 'x']
        )
        self.assertCountEqual(
            list(ds.keys()),
            ['dem', 'mask', 'veg_height', 'veg_k',
                'veg_tau', 'veg_type', 'projection']
        )

        self.compare_netcdf_files('topo.nc')


# class TestVegetationOptions(BasinSetupLakes):

#     EXTENTS = [318520.0, 4157550.0, 329470.0, 4167900.0]

#     @classmethod
#     def setUpClass(self):
#         self.subject = GenerateTopo(config_file=self.config_file)
#         self.subject.set_extents()

#     def test_landfire_140(self):
#         pass
