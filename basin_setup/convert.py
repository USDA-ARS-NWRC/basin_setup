import argparse
import time
from subprocess import check_output
import logging
import coloredlogs
from netCDF4 import Dataset

import os
from os.path import abspath, isdir, join
from . import __version__


def nc_masks_to_shp(fname, variables=None, output='output', debug=False):
    '''
    Converts all variables in a netcdf to shapefiles. If variables is left to
    default, the variable names will be populated with any variables containing
    key word mask.

    Args:
        fname: Path to a netcdf
        variables: List of variables in the netcdf to convert to shapefiles.
                   None is the default which will look for all variables
                   containing the keyword mask
        output: Folder to output the shapefiles. If it does not exist it will
            be created
    '''
    # Get logger and add color with a simple format
    if debug:
        level = 'DEBUG'
    else:
        level = 'INFO'

    log = logging.getLogger(__name__)
    coloredlogs.install(fmt='%(levelname)-5s %(message)s', level=level,
                        logger=log)
    # Print a nice header
    msg = "Basin Setup NetCDF Mask To Shapefile Tool v{0}".format(__version__)
    header = "=" * (len(msg) + 1)
    log.info(msg + "\n" + header + "\n")
    start = time.time()

    ds = Dataset(fname)

    # Check for none then check for lists
    if variables is None:
        log.info(
            "No variables provided, extracting all variables with keyword mask...")  # noqa
        variables = [v for v in ds.variables.keys() if 'mask' in v]

    elif not isinstance(variables, list):
        variables = [variables]

    # Create output folder if it doesn't exist
    output = abspath(output)
    if not isdir(output):
        log.debug("Creating output folder at {}...".format(output))
        os.mkdir(output)

    # Grab the file resolution for filenaming
    res = abs(ds.variables['x'][1] - ds.variables['x'][0])

    # Loop over all the variables and generate the string commands for
    # gdal_polygonize
    log.info("Extracting {} variables...".format(len(variables)))
    for v in variables:

        file_out = '{}_{:d}m.shp'.format(v.lower().replace(' ', '_'), int(res))
        file_out = join(output, file_out)

        cmd = 'gdal_polygonize.py NETCDF:"{}":"{}" -f "ESRI Shapefile" {}'.format(  # noqa
            fname, v, file_out)

        log.info(
            "Converting NETCDF variable {} to shapefile and outputting to {}".format(  # noqa
                v,
                file_out))
        log.debug("Executing:\n{}".format(cmd))

        check_output(cmd, shell=True)

    log.info("Finished! Elapsed {:d}s".format(int(time.time() - start)))


def nc_masks_to_shp_cli():
    '''
    Command line interface to the nc_masks to shapefiles function
    '''

    p = argparse.ArgumentParser(
        description='Exports netcdf masks as shapefiles')

    p.add_argument(
        "-f",
        "--file",
        required=True,
        dest='file',
        help="Path to a netcdf")
    p.add_argument("-v", "--variables", dest='variables', nargs='+',
                   default=None, help="Variables names in netcdf to output as"
                   " shapefiles, if left none, will default to all variables"
                   " with mask in their name")
    p.add_argument("-o", "--output", dest='output', default='output',
                   help="Name of a folder to output data, default is output")
    p.add_argument("-d", "--debug", dest="debug",
                   required=False, action='store_true')

    args = p.parse_args()

    nc_masks_to_shp(
        args.file,
        variables=args.variables,
        output=args.output,
        debug=args.debug
    )
