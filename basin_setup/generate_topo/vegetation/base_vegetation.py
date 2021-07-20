import logging
import os
import pathlib

import rioxarray
import xarray as xr

from basin_setup.utils import gdal


class BaseVegetation():
    """Base class for vegetation classes"""

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
        raise NotImplementedError('calculate_tau_and_k is not implemented')

    def calculate_height(self):
        raise NotImplementedError('calculate_height is not implemented')
