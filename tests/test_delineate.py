import os

from .basin_setup_test_case import BSTestCase


class TestDelineateCLI(BSTestCase):

    @classmethod
    def setUpClass(self):
        self.gfname = 'basin_outline.shp'
        self.cfname = self.gfname
        super().setUpClass()

        self.pour_points = os.path.join(self.data_path, 'pour_points.bna')
        self.dem = os.path.join(self.data_path, 'dem_epsg_32611_100m.tif')
        self.cmd_str = 'delineate -d {} -p {}  -o {}'.format(
            self.dem,
            self.pour_points,
            self.output
        )

    def test_ensemble(self):
        """
        Test the full run of the basin_setup command
        """
        self.run_test(self.cmd_str)
