import os
import unittest
from pathlib import Path
import basin_setup


class BasinSetupLakes(unittest.TestCase):

    BASE_INI_FILE_NAME = 'config.ini'

    test_dir = Path(basin_setup.__file__).parent.parent.joinpath('tests')
    basin_dir = test_dir.joinpath('Lakes')
    config_file = os.path.join(basin_dir, BASE_INI_FILE_NAME)
