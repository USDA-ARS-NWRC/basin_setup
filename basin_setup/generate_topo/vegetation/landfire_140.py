import pandas as pd
import numpy as np
import xarray as xr

from basin_setup.generate_topo.vegetation import BaseVegetation


class Landfire140(BaseVegetation):
    """Landfire 1.4.0"""

    # Files for the landfire dataset
    VEGETATION_TYPE = 'US_140EVT_20180618/Grid/us_140evt/hdr.adf'
    VEGETATION_HEIGHT = 'US_140EVH_20180618/Grid/us_140evh/hdr.adf'

    VEG_HEIGHT_CSV = 'US_140EVH_20180618/CSV_Data/LF_140EVH_05092014.csv'

    def __init__(self, config) -> None:
        super().__init__(config)

    def calculate_tau_and_k(self):

        # Open the key provided by Landfire to assign values in Tau and K
        veg_df = pd.read_csv(self.config['veg_params_csv'])
        veg_df.set_index('veg', inplace=True)

        # create NaN filled DataArray's to populate
        veg_tau = self.ds['type'].copy() * np.NaN
        veg_k = self.ds['type'].copy() * np.NaN

        veg_types = np.unique(self.ds['type'])

        for veg_type in veg_types:
            idx = self.ds['type'].values == veg_type
            veg_tau.values[idx] = veg_df.loc[veg_type, 'tau']
            veg_k.values[idx] = veg_df.loc[veg_type, 'k']

        if np.sum(np.isnan(veg_tau.values)) > 0:
            raise ValueError(
                'NaN values in veg_tau. Missing values in the veg_params_csv.')
        if np.sum(np.isnan(veg_k.values)) > 0:
            raise ValueError(
                'NaN values in veg_k. Missing values in the veg_params_csv.')

        self.tau_k = xr.combine_by_coords([
            veg_tau.to_dataset(name='veg_tau'),
            veg_k.to_dataset(name='veg_k')
        ])

    def calculate_height(self):

        veg_df = pd.read_csv(self.veg_height_csv)
        veg_df.set_index('VALUE', inplace=True)
        # use regex to pull out the numbers

        veg_height = self.ds['height'].copy()
