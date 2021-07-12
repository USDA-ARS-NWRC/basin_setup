import sys
import os

from inicheck.config import UserConfig
from inicheck.output import print_config_report
from inicheck.tools import check_config, get_user_config


def read(config):
    """Read an inicheck config file and return the user config

    Args:
        config (str or UserConfig): file name or Userconfig object

    Raises:
        Exception: If file does not exist
        Exception: config is not a file or UserConfig

    Returns:
        tuple: (Userconfig, config file name)
    """

    # read the config file and store
    if isinstance(config, str):
        if not os.path.isfile(config):
            raise Exception('Configuration file does not exist --> {}'
                            .format(config))
        configFile = config

        # Read in the original users config
        ucfg = get_user_config(config, modules='basin_setup')

    elif isinstance(config, UserConfig):
        ucfg = config
        configFile = config.filename

    else:
        raise Exception('Config passed to basin_setup is neither file name'
                        ' nor UserConfig instance')

    return ucfg, configFile


def check(config, logger):
    """Check the config file for problems

    Args:
        config (UserConfig): UserConfig object to check
        logger (logger): logger instance to send messages to
    """

    # Check the user config file for errors and report issues if any
    logger.info("Checking config file for issues...")
    warnings, errors = check_config(config)
    print_config_report(warnings, errors, logger=logger)

    # Exit SMRF if config file has errors
    if len(errors) > 0:
        logger.error("Errors in the config file. See configuration"
                     " status report above.")
        sys.exit()
