import os
import sys
import logging

from inicheck.config import UserConfig
from inicheck.output import print_config_report
from inicheck.tools import check_config, get_user_config


class GenerateTopo():

    def __init__(self, config_file):

        self.read_config(config_file)

    def read_config(self, config):

        # read the config file and store
        if isinstance(config, str):
            if not os.path.isfile(config):
                raise Exception('Configuration file does not exist --> {}'
                                .format(config))
            self.configFile = config

            # Read in the original users config
            ucfg = get_user_config(config, modules='basin_setup')

        elif isinstance(config, UserConfig):
            ucfg = config
            self.configFile = config.filename

        else:
            raise Exception('Config passed to basin_setup is neither file name'
                            ' nor UserConfig instance')

        # Check the user config file for errors and report issues if any
        self._logger.info("Checking config file for issues...")
        warnings, errors = check_config(ucfg)
        print_config_report(warnings, errors, logger=self._logger)
        self.ucfg = ucfg
        self.config = self.ucfg.cfg

        # Exit SMRF if config file has errors
        if len(errors) > 0:
            self._logger.error("Errors in the config file. See configuration"
                               " status report above.")
            sys.exit()
