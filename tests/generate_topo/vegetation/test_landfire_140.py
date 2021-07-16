import xarray as xr

from basin_setup.generate_topo.vegetation import Landfire140
from basin_setup.utils import domain_extent

from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestLandfire140(BasinSetupLakes):

    EXTENTS = [318520.0, 4157550.0, 329470.0, 4167900.0]
    CELL_SIZE = 150
    CRS = 'EPSG:32611'

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        config = self.base_config_copy()
        self.subject = Landfire140(config.cfg['generate_topo'])

    def test_init(self):
        self.assertIsInstance(self.subject.config, dict)

    def test_reproject(self):
        self.subject.reproject(self.EXTENTS, self.CELL_SIZE, self.CRS)

        for image in self.subject.clipped_images.values():
            extents, cell_size = domain_extent.parse_from_file(image)
            self.assertListEqual(extents, self.EXTENTS)
            self.assertTrue(cell_size == self.CELL_SIZE)

        self.assertIsInstance(self.subject.ds, xr.Dataset)

    def test_calculate_tau_and_k(self):
        self.subject.reproject(self.EXTENTS, self.CELL_SIZE, self.CRS)
        self.subject.calculate_tau_and_k()
        self.assertIsInstance(self.subject.veg_tau_k, xr.Dataset)

    def test_calculate_height(self):
        self.subject.reproject(self.EXTENTS, self.CELL_SIZE, self.CRS)
        self.subject.calculate_height()
        self.assertIsInstance(self.subject.veg_height, xr.DataArray)
