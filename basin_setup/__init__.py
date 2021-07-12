import os

__veg_parameters__ = os.path.join(
    os.path.dirname(__file__),
    "landfire_veg_param.csv")
__version__ = "0.14.6"

__core_config__ = os.path.abspath(
    os.path.dirname(__file__) + '/CoreConfig.ini')
__recipes__ = os.path.abspath(
    os.path.dirname(__file__) + '/recipes.ini')
