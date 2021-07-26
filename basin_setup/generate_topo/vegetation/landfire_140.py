import re

import numpy as np
import pandas as pd
import xarray as xr

from basin_setup.generate_topo.vegetation import BaseVegetation


class Landfire140(BaseVegetation):
    """Landfire 1.4.0"""

    DATASET = 'landfire140'

    # Files for the landfire dataset
    VEGETATION_TYPE = 'US_140EVT_20180618/Grid/us_140evt/hdr.adf'
    VEGETATION_HEIGHT = 'US_140EVH_20180618/Grid/us_140evh/hdr.adf'

    VEG_HEIGHT_CSV = 'US_140EVH_20180618/CSV_Data/LF_140EVH_05092014.csv'

    def __init__(self, config) -> None:
        super().__init__(config)

    def calculate_height(self):

        self._logger.debug('Calculating veg height')

        veg_df = pd.read_csv(self.veg_height_csv)
        veg_df.set_index('VALUE', inplace=True)

        # match whole numbers and decimals in the line
        regex = re.compile(r"(?<!\*)(\d*\.?\d+)(?!\*)")
        veg_df['height'] = 0  # see assumption below
        for idx, row in veg_df.iterrows():
            matches = regex.findall(row.CLASSNAMES)
            if len(matches) > 0:
                veg_df.loc[idx, 'height'] = np.mean(
                    np.array([float(x) for x in matches]))

        # create an image that is full of 0 values. This makes the assumption
        # that any value that is not found in the csv file will have a
        # height of 0 meters. This will work most of the time except in
        # developed or agriculture but there isn't snow there anyways...
        height = self.ds['veg_height'].copy() * 0
        veg_heights = np.unique(self.ds['veg_height'])

        for veg_height in veg_heights:
            idx = self.ds['veg_height'].values == veg_height

            if veg_height in veg_df.index:
                height.values[idx] = veg_df.loc[veg_height, 'height']

        # sanity check
        assert np.sum(np.isnan(height.values)) == 0

        self.veg_height = height
