import os

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = 'unknown'


__veg_parameters__ = os.path.join(
    os.path.dirname(__file__),
    'generate_topo',
    'vegetation',
    'landfire_veg_param.csv'
)

__core_config__ = os.path.abspath(
    os.path.dirname(__file__) + '/CoreConfig.ini')
__recipes__ = os.path.abspath(
    os.path.dirname(__file__) + '/recipes.ini')
