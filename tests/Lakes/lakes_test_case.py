import os
import unittest
from pathlib import Path
from copy import deepcopy
from inicheck.tools import cast_all_variables, get_user_config

import basin_setup


class BasinSetupLakes(unittest.TestCase):

    BASE_INI_FILE_NAME = 'config.ini'

    test_dir = Path(basin_setup.__file__).parent.parent.joinpath('tests')
    basin_dir = test_dir.joinpath('Lakes')
    config_file = os.path.join(basin_dir, BASE_INI_FILE_NAME)

    @classmethod
    def base_config_copy(cls):
        return deepcopy(cls._base_config)

    @classmethod
    def load_base_config(cls):
        cls._base_config = get_user_config(
            cls.config_file, modules='basin_setup')

    @classmethod
    def setUpClass(cls):
        cls.load_base_config()
