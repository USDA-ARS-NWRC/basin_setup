import logging
import os
import pathlib
import re

import pandas as pd
import numpy as np
import rioxarray
import xarray as xr

from basin_setup.utils import gdal


class BaseVegetation():
    """Base class for vegetation classes"""

    VEG_IMAGES = [
        'veg_type',
        'veg_tau',
        'veg_k',
        'veg_height'
    ]

    def __init__(self, config) -> None:

        self._logger = logging.getLogger(self.__class__.__module__)
        self.config = config

        if self.config['veg_params_csv'] is None:
            self.config['veg_params_csv'] = os.path.join(
                pathlib.Path(__file__).parent.absolute(),
                'landfire_veg_param.csv'
            )

        self.debug = self.config['leave_intermediate_files']
        self.temp_dir = os.path.join(self.config['output_folder'], 'temp')

    @property
    def veg_type_image(self):
        return os.path.join(
            self.config['vegetation_folder'],
            self.VEGETATION_TYPE
        )

    @property
    def veg_height_image(self):
        return os.path.join(
            self.config['vegetation_folder'],
            self.VEGETATION_HEIGHT
        )

    @property
    def veg_height_csv(self):
        return os.path.join(
            self.config['vegetation_folder'],
            self.VEG_HEIGHT_CSV
        )

    @property
    def clipped_images(self):
        return {
            'veg_type': os.path.join(self.temp_dir, 'clipped_veg_type.tif'),
            'veg_height': os.path.join(self.temp_dir, 'clipped_veg_height.tif')
        }

    def reproject(self, extents, cell_size, target_crs) -> None:
        """reproject vegetation datasets to the desired extents.

        Args:
            extents (list): Extents to crop to [left, bottom, right, top]
            cell_size (float): cell size to resample to
            target_crs (str): EPSG code, i.e. EPSG:32611
            resample (str, optional): resampling method for veg height
                Defaults to 'bilinear'.
        """

        self._logger.debug(
            'Reprojecting and clipping veg type and height datasets')

        # vegetation type
        gdal.gdalwarp(
            self.veg_type_image,
            self.clipped_images['veg_type'],
            target_crs,
            extents,
            cell_size,
            resample='mode',
            logger=self._logger
        )

        # vegetation height
        gdal.gdalwarp(
            self.veg_height_image,
            self.clipped_images['veg_height'],
            target_crs,
            extents,
            cell_size,
            resample='mode',
            logger=self._logger
        )

    def load_clipped_images(self):
        """Load the clipped images from gdalwarp into a xr.Dataset
        """

        # load into xarray dataset
        da = []
        for dataset, image in self.clipped_images.items():
            da.append(rioxarray.open_rasterio(image, default_name=dataset))

            if not self.debug:
                os.remove(image)

        da = [w.to_dataset() for w in da]
        self.ds = xr.combine_by_coords(da)
        self.ds = self.ds.squeeze('band')
        self.ds = self.ds.drop_vars('band')

    def calculate_tau_and_k(self):
        """Populate an image of veg_tau and veg_k from the vegitation parameters
        csv file.

        Raises:
            ValueError: If there are missing classes in the csv file
        """

        self._logger.debug('Calculating veg tau and k')

        # Open the key provided by Landfire to assign values in Tau and K
        veg_df = pd.read_csv(self.config['veg_params_csv'])
        veg_df.set_index(self.DATASET, inplace=True)

        # create NaN filled DataArray's to populate
        veg_tau = self.ds['veg_type'].copy() * np.NaN
        veg_k = self.ds['veg_type'].copy() * np.NaN

        # check for missing values
        veg_types = np.unique(self.ds['veg_type'])
        check = veg_df.loc[veg_types, 'tau']
        missing = check[check.isnull()]

        if len(missing) > 0:
            raise ValueError(
                'Missing tau/k for the following veg type classes: {}'.format(
                    list(missing.index)
                ))

        for veg_type in veg_types:
            idx = self.ds['veg_type'].values == veg_type
            veg_tau.values[idx] = veg_df.loc[veg_type, 'tau']
            veg_k.values[idx] = veg_df.loc[veg_type, 'k']

        # sanity check to make sure that there are no NaN values in the images
        assert np.sum(np.isnan(veg_tau.values)) == 0
        assert np.sum(np.isnan(veg_k.values)) == 0

        self.veg_tau_k = xr.combine_by_coords([
            self.ds['veg_type'].to_dataset(),
            veg_tau.to_dataset(name='veg_tau'),
            veg_k.to_dataset(name='veg_k')
        ])

        # set the attributes for the layers
        self.veg_tau_k['veg_type'].attrs = {'long_name': 'vegetation type'}
        self.veg_tau_k['veg_tau'].attrs = {'long_name': 'vegetation tau'}
        self.veg_tau_k['veg_k'].attrs = {'long_name': 'vegetation k'}

    def calculate_height(self):
        """Parse the Landfire csv files for vegetation height
        """

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
        self.veg_height.attrs = {'long_name': 'vegetation height'}

    def set_attributes(self):
        """Set the attributes for the layers"""

        self.veg_tau_k['veg_type'].attrs = {'long_name': 'vegetation type'}
        self.veg_tau_k['veg_tau'].attrs = {'long_name': 'vegetation tau'}
        self.veg_tau_k['veg_k'].attrs = {'long_name': 'vegetation k'}
        self.veg_height.attrs = {'long_name': 'vegetation height'}

    def empty(self, dem):
        """Create empty data arrays when no vegetation dataset is used

        Args:
            dem (xr.DataArray): DataArray for the dem to copy off
        """

        images = []
        for image in self.VEG_IMAGES:
            veg = dem.copy() * np.NaN
            veg.name = image
            images.append(veg.to_dataset())

        self.veg_tau_k = xr.combine_by_coords(images[:3])
        self.veg_height = images[-1]['veg_height']
