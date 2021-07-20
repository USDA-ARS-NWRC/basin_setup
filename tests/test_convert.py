import os

from .basin_setup_test_case import BSTestCase


class TestConvertCLI(BSTestCase):

    @classmethod
    def setUpClass(self):
        self.gfname = 'mask_150m.shp'
        self.cfname = self.gfname

        super().setUpClass()
        self.topo = os.path.join(self.gold_path, 'topo.nc')
        self.cmd_str = 'nc2shp -f {} -o {}'

    def test_nc2shp_no_variables(self):
        '''
        Run the nc2shp command without variables
        '''
        # Attempt to export all the masks
        cmd = self.cmd_str.format(self.topo, self.output)
        self.run_test(cmd)

    def test_nc2shp_w_variables(self):
        '''
        Run the nc2shp command with variables
        '''
        # Attempt to export the basin masks
        cmd = self.cmd_str.format(self.topo, self.output)
        self.run_test(cmd)
