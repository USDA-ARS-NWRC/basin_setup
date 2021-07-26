from basin_setup.generate_topo.vegetation import BaseVegetation


class Landfire200(BaseVegetation):
    """Landfire 2.0.0"""

    DATASET = 'landfire200'

    # Files for the landfire dataset
    VEGETATION_TYPE = 'LF2016_EVT_200_CONUS/LF2016_EVT_200_CONUS/Tif/LC16_EVT_200.tif'  # noqa
    VEGETATION_HEIGHT = 'LF2016_EVH_200_CONUS/LF2016_EVH_200_CONUS/Tif/LC16_EVH_200.tif'  # noqa

    VEG_HEIGHT_CSV = 'LF2016_EVH_200_CONUS/LF2016_EVH_200_CONUS/CSV_Data/LF16_EVH_200.csv'  # noqa

    def __init__(self, config) -> None:
        super().__init__(config)
