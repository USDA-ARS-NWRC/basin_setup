from inicheck.config import UserConfig
from rasterio import Affine

from basin_setup.generate_topo import GenerateTopo
from basin_setup.generate_topo.shapefile import Shapefile

from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestBasinSetup(BasinSetupLakes):

    @classmethod
    def setUpClass(self):
        self.subject = GenerateTopo(config_file=self.config_file)

    def test_init(self):
        self.assertIsInstance(self.subject.ucfg, UserConfig)

    def test_set_extents(self):
        self.subject.set_extents()
        self.assertListEqual(
            self.subject.extents,
            [320320.405027, 4158537.07547, 327520.405027, 4166337.07547]
        )
        self.assertIsInstance(self.subject.transform, Affine)
        self.assertTrue(len(self.subject.x) == 144)
        self.assertTrue(len(self.subject.y) == 156)

    def test_load_basin_shapefiles(self):
        self.subject.load_basin_shapefiles()

        self.assertTrue(len(self.subject.basin_shapefiles) == 1)
        self.assertIsInstance(self.subject.basin_shapefiles[0], Shapefile)
        self.assertTrue(self.subject.basin_shapefiles[0].epsg == '32611')
