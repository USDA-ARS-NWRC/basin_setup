from unittest.mock import patch

import numpy as np
import xarray as xr
from inicheck.tools import cast_all_variables

from basin_setup.generate_topo import GenerateTopo
from basin_setup.generate_topo.vegetation import Landfire140, Landfire200
from tests.Lakes.lakes_test_case import BasinSetupLakes


@patch.object(Landfire140, 'veg_height_csv',
              new='tests/Lakes/data/landfire_1.4.0/LF_140EVH_05092014.csv')
@patch.object(Landfire140, 'clipped_images', new={
    'veg_type': 'tests/Lakes/data/landfire_1.4.0/clipped_veg_type.tif',
    'veg_height': 'tests/Lakes/data/landfire_1.4.0/clipped_veg_height.tif'
})
@patch.object(Landfire200, 'veg_height_csv',
              new='tests/Lakes/data/landfire_2.0.0/LF16_EVH_200.csv')
@patch.object(Landfire200, 'clipped_images', new={
    'veg_type': 'tests/Lakes/data/landfire_2.0.0/clipped_veg_type.tif',
    'veg_height': 'tests/Lakes/data/landfire_2.0.0/clipped_veg_height.tif'
})
class TestVegetationOptions(BasinSetupLakes):

    @patch.object(Landfire140, 'reproject', return_value=True)
    def test_landfire_140(self, mock_reproject):
        gt = GenerateTopo(config_file=self.config_file)
        gt.run()
        self.assertTrue(mock_reproject.called)
        self.assertTrue(mock_reproject.call_count == 1)

        ds = xr.open_dataset(self.output_topo, cache=False)

        self.assertCountEqual(
            list(ds.coords.keys()),
            ['y', 'x']
        )
        self.assertCountEqual(
            list(ds.keys()),
            ['dem', 'mask', 'veg_height', 'veg_k',
                'veg_tau', 'veg_type', 'projection']
        )
        ds.close()

        self.compare_netcdf_files('landfire_140/topo.nc', 'topo.nc')

    @patch.object(Landfire200, 'reproject', return_value=True)
    def test_landfire_200(self, mock_reproject):
        config = self.base_config_copy()

        config.raw_cfg['generate_topo']['vegetation_dataset'] = 'landfire_2.0.0'  # noqa
        config.raw_cfg['generate_topo']['vegetation_folder'] = '../../landfire/landfire_200'  # noqa

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        gt = GenerateTopo(config_file=config)
        gt.run()
        self.assertTrue(mock_reproject.called)
        self.assertTrue(mock_reproject.call_count == 1)

        ds = xr.open_dataset(self.output_topo, cache=False)

        self.assertCountEqual(
            list(ds.coords.keys()),
            ['y', 'x']
        )
        self.assertCountEqual(
            list(ds.keys()),
            ['dem', 'mask', 'veg_height', 'veg_k',
                'veg_tau', 'veg_type', 'projection']
        )
        ds.close()

        self.compare_netcdf_files('landfire_200/topo.nc', 'topo.nc')

    @patch.object(Landfire140, 'reproject', return_value=True)
    def test_no_veg(self, mock_reproject):
        gt = GenerateTopo(config_file=self.config_file)
        gt.config['vegetation_dataset'] = None
        gt.run()

        self.assertFalse(mock_reproject.called)
        self.assertTrue(mock_reproject.call_count == 0)

        ds = xr.open_dataset(self.output_topo, cache=False)

        self.assertCountEqual(
            list(ds.coords.keys()),
            ['y', 'x']
        )
        self.assertCountEqual(
            list(ds.keys()),
            ['dem', 'mask', 'veg_height', 'veg_k',
                'veg_tau', 'veg_type', 'projection']
        )
        ds.close()

        for image in gt.veg.VEG_IMAGES:
            if image == 'veg_type':
                # all veg type are 0 values
                self.assertTrue(np.sum(ds[image].isnull().values) == 0)
            else:
                self.assertTrue(np.all(ds[image].isnull().values))
