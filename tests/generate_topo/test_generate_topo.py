from inicheck.config import UserConfig
from rasterio import Affine

from basin_setup.generate_topo import GenerateTopo
from basin_setup.generate_topo.shapefile import Shapefile
from basin_setup.utils import domain_extent
from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestBasinSetup(BasinSetupLakes):

    EXTENTS = [318520.0, 4157550.0, 329470.0, 4167900.0]

    @classmethod
    def setUpClass(self):
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
        self.assertTrue(len(self.subject.x) == 73)
        self.assertTrue(len(self.subject.y) == 69)

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

        self.assertListEqual(extents, self.EXTENTS)
        self.assertTrue(cell_size == self.subject.config['cell_size'])
