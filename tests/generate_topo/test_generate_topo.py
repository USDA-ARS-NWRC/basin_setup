from inicheck.config import UserConfig

from basin_setup.generate_topo import GenerateTopo

from tests.Lakes.lakes_test_case import BasinSetupLakes


class TestBasinSetup(BasinSetupLakes):

    def test_init(self):
        gt = GenerateTopo(config_file=self.config_file)
        self.assertIsInstance(gt.ucfg, UserConfig)

    # def test_run(self):
    #     gt = GenerateTopo(config_file=self.config_file)
    #     gt.run()
    #     gt.topo
