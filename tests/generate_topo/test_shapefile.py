import numpy as np

from basin_setup.generate_topo.shapefile import Shapefile
from basin_setup.utils import domain_extent
from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestShapefile(BasinSetupLakes):

    NX = 144
    NY = 156
    EXTENTS = [320320.405027, 4158537.07547, 327520.405027, 4166337.07547]
    CELL_SIZE = 50

    @classmethod
    def setUpClass(self):
        self.shape = Shapefile('tests/Lakes/gold/basin_outline.shp')

    def test_load(self):
        self.assertIsInstance(self.shape, Shapefile)
        self.assertTrue(len(self.shape.polygon) == 1)

    def test_crs(self):
        self.assertEqual(self.shape.crs, self.CRS)

    def test_mask(self):
        transform, x, y = domain_extent.affine_transform_from_extents(
            self.EXTENTS, self.CELL_SIZE)
        mask = self.shape.mask(self.NX, self.NY, transform)
        self.assertTrue(mask.shape == (self.NY, self.NX))
        self.assertTrue(np.sum(mask == 1) == 11188)
