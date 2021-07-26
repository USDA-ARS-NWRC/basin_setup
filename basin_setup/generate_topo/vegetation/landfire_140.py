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
