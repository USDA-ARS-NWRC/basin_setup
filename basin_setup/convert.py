from netCDF4 import Dataset
from subprocess import check_output
from basin_setup.basin_setup import Messages
import time
import argparse

DEBUG = True

def nc_masks_to_shp(fname, variables=None):
    '''
    Converts all variables in a netcdf to shapefiles. If variables is left to
    default, the variable names will be populated with any variables containing
    key word mask.

    Args:
        fname: Path to a netcdf
        variables: List of variables in the netcdf to convert to shapefiles.
                   None is the default which will look for all variables
                   containing the keyword mask
    '''
    out = Messages()
    start = time.time()

    ds = Dataset(fname)

    # Check for none then check for lists
    if variables is None:
        out.msg("No variables provided, extracting all variables with keyword mask..")
        variables = [v for v in ds.variables.keys() if 'mask' in v]

    elif type(variables) != list:
        variables = [variables]

    # Grab the file resolution for filenaming
    res = abs(ds.variables['x'][1] - ds.variables['x'][0])

    # Loop over all the variables and generate the string commands for gdal_polygonize
    out.msg("Extracting {} varaibles...".format(len(variables)))
    for v in variables:

        file_out = '{}_{:d}m.shp'.format(v.lower().replace(' ','_'), int(res))
        cmd  = 'gdal_polygonize.py -f "ESRI Shapefile" NETCDF:"{}":"{}" {}'.format(fname, v, file_out)

        out.msg("Converting NETCDF variable {} to shapefile and outputting to {}".format(v, file_out))
        out.dbg("Executing:\n{}".format(cmd))

        s = check_output(cmd, shell=True)

    out.msg("Finished! Elapsed {:d}s".format(int(time.time() - start)))

def nc_masks_to_shp_cli():
    '''
    Command line interface to the nc_masks to shapefiles function
    '''

    p = argparse.ArgumentParser(description='Exports netcdf masks as shapefiles')

    p.add_argument("-f", "--file", required=True, dest='file', help="Path to a netcdf")
    p.add_argument("-v", "--variables", dest='variables', nargs='+',
                  default=None, help="Variables names in netcdf to output as"
                  " shapefiles, if left none, will default to all variables"
                  " with mask in their name")
    args = p.parse_args()
    nc_masks_to_shp(args.file, variables=args.variables)
