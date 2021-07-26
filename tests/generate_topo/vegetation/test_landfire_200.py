import os
from unittest.mock import patch

from inicheck.tools import cast_all_variables
import xarray as xr

from basin_setup.generate_topo.vegetation import Landfire200
from basin_setup.utils import domain_extent
from tests.Lakes.lakes_test_case import BasinSetupLakes


# patch the landfire datasets for testing. Comment out to test with the
# real thing
@patch.object(Landfire200, 'veg_height_csv',
              new='tests/Lakes/data/landfire_2.0.0/LF16_EVH_200.csv')
@patch.object(Landfire200, 'clipped_images', new={
    'veg_type': 'tests/Lakes/data/landfire_2.0.0/clipped_veg_type.tif',
    'veg_height': 'tests/Lakes/data/landfire_2.0.0/clipped_veg_height.tif'
})
class TestLandfire200(BasinSetupLakes):

    # TODO change extents to this instead of decimals
    # EXTENTS = [318520.0, 4157550.0, 329470.0, 4167900.0]
    EXTENTS = [319570.405027, 4157787.07547, 328270.405027, 4167087.07547]
    EXTENTS_RASTER = [319570.405, 4157787.075, 328270.405, 4167087.075]

    CELL_SIZE = 150
    CRS = 'EPSG:32611'

    @ classmethod
    def setUpClass(self):
        super().setUpClass()
        config = self.base_config_copy()

        config.raw_cfg['generate_topo']['vegetation_dataset'] = 'landfire_2.0.0'  # noqa
        config.raw_cfg['generate_topo']['vegetation_folder'] = '../../landfire/landfire_200'  # noqa

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        self.subject = Landfire200(config.cfg['generate_topo'])

        os.makedirs(self.subject.temp_dir, exist_ok=True)

    def test_init(self):
        self.assertIsInstance(self.subject.config, dict)

    @patch.object(Landfire200, 'reproject', return_value=True)
    def test_reproject(self, mock_veg):
        self.subject.reproject(self.EXTENTS, self.CELL_SIZE, self.CRS)

        for image in self.subject.clipped_images.values():
            extents, cell_size = domain_extent.parse_from_file(image)
            self.assertListEqual(extents, self.EXTENTS_RASTER)
            self.assertTrue(cell_size == self.CELL_SIZE)

    def test_load_clipped_images(self):
        self.subject.load_clipped_images()
        self.assertIsInstance(self.subject.ds, xr.Dataset)

    def test_calculate_tau_and_k(self):
        self.subject.load_clipped_images()
        self.subject.calculate_tau_and_k()
        self.assertIsInstance(self.subject.veg_tau_k, xr.Dataset)
        self.assertCountEqual(
            list(self.subject.veg_tau_k.coords.keys()),
            ['y', 'x', 'spatial_ref']
        )
        self.assertCountEqual(
            list(self.subject.veg_tau_k.keys()),
            ['veg_k', 'veg_tau', 'veg_type']
        )

    def test_calculate_height(self):
        self.subject.load_clipped_images()
        self.subject.calculate_height()
        self.assertIsInstance(self.subject.veg_height, xr.DataArray)
        self.assertCountEqual(
            list(self.subject.veg_height.coords.keys()),
            ['y', 'x', 'spatial_ref']
        )
