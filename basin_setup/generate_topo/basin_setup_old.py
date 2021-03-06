#!/usr/bin/env python3

import argparse
import io
import os
import sys
import urllib
import zipfile
from datetime import datetime
from os.path import abspath, basename, dirname, expanduser, isdir, isfile, join
from shutil import copyfile, rmtree
from subprocess import PIPE, Popen, check_output

import numpy as np
import pandas as pd
import requests
import shapefile
from colorama import Fore, Style, init
from netCDF4 import Dataset
from shapely import geometry
from spatialnc.proj import add_proj
from spatialnc.utilities import strip_chars

from basin_setup import __veg_parameters__, __version__

# Initialize colors
init()

DEBUG = False


class Messages():
    def __init__(self):
        self.context = {'warning': Fore.YELLOW,
                        'error': Fore.RED,
                        'ok': Fore.GREEN,
                        'normal': Style.NORMAL + Fore.WHITE,
                        'header': Style.BRIGHT}

    def build_msg(self, str_msg, context_str=None):
        """
        Constructs the desired strings for color and Style

        Args;
            str_msg: String the user wants to output
            context_str: type of print style and color, key associated with
                         self.context
        Returns:
            final_msg: Str containing the desired colors and styles
        """

        if context_str is None:
            context_str = 'normal'

        if context_str in self.context.keys():
            if isinstance(str_msg, list):
                str_msg = ', '.join([str(s) for s in str_msg])

            final_msg = self.context[context_str] + str_msg + Style.RESET_ALL
        else:
            raise ValueError("Not a valid context")
        return final_msg

    def _structure_msg(self, a_msg):
        if isinstance(a_msg, list):
            a_msg = ', '.join([str(s) for s in a_msg])

        if not isinstance(a_msg, str):
            a_msg = str(a_msg)

        return a_msg

    def msg(self, str_msg, context_str=None):
        final_msg = self.build_msg(str_msg, context_str)
        print('\n' + final_msg)

    def dbg(self, str_msg, context_str=None):
        """
        Messages designed for debugging set by a global variable DEBUG
        """
        if DEBUG:
            final_msg = self.build_msg('[DEBUG]: ', 'header')
            final_msg += self._structure_msg(str_msg)
            final_msg = self.build_msg(final_msg, context_str)
            print('\n' + final_msg)

    def warn(self, str_msg):
        final_msg = self.build_msg('[WARNING]: ', 'header')
        final_msg = self.build_msg(final_msg + str_msg, 'warning')
        print('\n' + final_msg)

    def error(self, str_msg):
        final_msg = self.build_msg('[ERROR]: ', 'header')
        final_msg = self.build_msg(final_msg + str_msg, 'error')
        print('\n' + final_msg)

    def respond(self, str_msg):
        """
        Messages acting like a confirmation to the user and in response to the
        previous message
        """
        final_msg = self.build_msg(str_msg, 'ok')
        print('\t' + final_msg)


out = Messages()


def proper_name(name):
    name = name.replace('_', " ")
    name = ' '.join([c.capitalize() for c in name.split(' ')])
    return name


def is_float(str_val):
    try:
        float(str_val)
        return True
    except BaseException:
        return False


def shapely_to_pyshp(shapelygeom):
    """
    Convert shapely objects to be used by shapefile
    Adapted from https://gis.stackexchange.com/a/86738/110039
    """

    try:
        shapelytogeojson = shapely.geometry.mapping  # noqa
    except BaseException:
        import shapely.geometry
        shapelytogeojson = shapely.geometry.mapping
    geoj = shapelytogeojson(shapelygeom)
    # create empty pyshp shape
    record = shapefile._Shape()
    # set shapetype
    if geoj["type"] == "Null":
        pyshptype = 0
    elif geoj["type"] == "Point":
        pyshptype = 1
    elif geoj["type"] == "LineString":
        pyshptype = 3
    elif geoj["type"] == "Polygon":
        pyshptype = 5
    elif geoj["type"] == "MultiPoint":
        pyshptype = 8
    elif geoj["type"] == "MultiLineString":
        pyshptype = 3
    elif geoj["type"] == "MultiPolygon":
        pyshptype = 5
    record.shapeType = pyshptype
    # set points and parts
    if geoj["type"] == "Point":
        record.points = geoj["coordinates"]
        record.parts = [0]
    elif geoj["type"] in ("MultiPoint", "Linestring"):
        record.points = geoj["coordinates"]
        record.parts = [0]
    elif geoj["type"] == "Polygon":
        index = 0
        points = []
        parts = []
        for eachmulti in geoj["coordinates"]:
            points.extend(eachmulti)
            parts.append(index)
            index += len(eachmulti)
        record.points = points
        record.parts = parts
    elif geoj["type"] in ("MultiPolygon", "MultiLineString"):
        index = 0
        points = []
        parts = []
        for polygon in geoj["coordinates"]:
            for part in polygon:
                points.extend(part)
                parts.append(index)
                index += len(part)
        record.points = points
        record.parts = parts

    return record


def condition_extent(extent, cell_size):
    """
    Checks if there is a mismatch in the domain size and cell size. Expands the
    domain so cells fit evenly.

    Args:
        extent: A list of 4 values representing the domain in
            left,bottom, right,top
        cell_size: integer of the resolution
    Returns:
        result: a list of 4 values representing the domain with evenly
            fitting cells
    """
    result = []
    rl_adjustment = 0.
    tb_adjustment = 0.

    # Calculate the cell modulus
    rl_mod = (extent[2] - extent[0]) % cell_size
    tb_mod = (extent[3] - extent[1]) % cell_size

    if rl_mod > 0:
        rl_adjustment = (cell_size - rl_mod) / 2.0
    if tb_mod > 0:
        tb_adjustment = (cell_size - tb_mod) / 2.0

    out.dbg("Checking how well the cell size is fitted to the domain:"
            "\t\nRight-Left modulo: {0:.2f}"
            "\t\nTop - Bottom modulo: {1:.2f}".format(rl_mod, tb_mod))

    # Adjust in both directions to maintain common center
    result.append(extent[0] - rl_adjustment)  # Left
    result.append(extent[1] - tb_adjustment)  # Bottom
    result.append(extent[2] + rl_adjustment)  # Right
    result.append(extent[3] + tb_adjustment)  # Top
    rl_mod = (result[2] - result[0]) % cell_size  # Modulus right to left
    tb_mod = (result[3] - result[1]) % cell_size  # Modulus top to bottom

    if rl_adjustment != 0 or tb_adjustment != 0:
        out.warn(" Modeling domain extents are ill fit for cell size {}."
                 "\nExpanding to fit whole cells...".format(cell_size))

        out.dbg("Checking how well our cell size is fitted to our domain:"
                "\t\nRight-Left modulo: {0:.2f}"
                "\t\nTop - Bottom modulo: {1:.2f}".format(rl_mod, tb_mod))

    return result


def parse_extent(fname, cellsize_return=False, x_field='x', y_field='y'):
    """
    Author: Micah Johnson, mod. by Ernesto Trujillo
    Uses ogr to parse the information of some GIS file and returns a list of
    the response of the things important to this script.

    Args:
        fname: Full path point to file containing GIS information
        cellsize_return: Optional (deafault = False). True will add cellsize
            as the last element of the return list. Option only for '.asc'
            and '.nc' data types

    Returns:
        extent: containing images extent in list type
        [x_ll, y_ll, x_ur, y_ur, cellsize (optional)]
    """
    file_type = fname.split('.')[-1]
    if file_type == 'shp':
        basin_shp_info = check_output(['ogrinfo', '-al', fname],
                                      universal_newlines=True)
        parse_list = basin_shp_info.split('\n')

        # Parse extents from basin info
        for line in parse_list:
            if 'extent:' in line.lower():
                k, v = line.split(':')
                parseable = v.replace(' - ', ',')
                parseable = ''.join(c for c in parseable if c not in ' ()\n')

                try:
                    extent = [float(i) for i in parseable.split(',')]
                except Exception as e:
                    print("Attempting to evaluate extent on {} from the line "
                          "-->  {}".format(fname, parseable))
                    raise(e)

                break

    elif file_type == 'tif':
        basin_shp_info = check_output(['gdalinfo', fname],
                                      universal_newlines=True)
        parse_list = basin_shp_info.split('\n')
        extent = []
        for line in parse_list:
            ll = line.lower()

            # Look for the kw pixel
            if 'pixel size' in ll:
                # Should find an equals
                if "=" in ll:
                    v = ll.split("=")[-1]
                    w = ''.join(c for c in v if c not in ' ()\n')
                    cellsize = float(w.split(',')[0])

            if 'lower left' in ll or 'upper right' in ll:
                for w in line.split(' '):
                    try:
                        if len(extent) <= 4:
                            parseable = \
                                ''.join(c for c in w if c not in ' ,()\n')
                            extent.append(float(parseable))
                    except BaseException:
                        pass

        if cellsize_return:
            extent.append(cellsize)

    elif file_type == 'asc':

        ascii_file = open(fname, 'r')

        ascii_headlines = []
        ascii_headlines = [ascii_file.readline().strip('\n')
                           for i_line in range(6)]
        ascii_file.close()

        parse_list = ascii_headlines
        extent = []
        n_rows = 0
        n_cols = 0
        x_ll = 0
        y_ll = 0
        cellsize = 0

        for line in parse_list:
            ll = line.lower()
            w = line.split(' ')
            if 'xllcorner' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                x_ll = float(w[-1])
            elif 'yllcorner' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                y_ll = float(w[-1])
            elif 'ncols' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                n_cols = float(w[-1])
            elif 'nrows' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                n_rows = float(w[-1])
            elif 'cellsize' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                cellsize = float(w[-1])

            extent = [x_ll, y_ll,
                      x_ll + (n_cols) * cellsize,
                      y_ll + (n_rows) * cellsize]

            if cellsize_return:
                extent.append(cellsize)

    elif file_type == 'nc':

        ncfile = Dataset(fname, 'r')

        # Extract fields of interest
        try:
            x_vector = ncfile.variables[x_field][:]
        except KeyError:
            print('KeyError: x_field key not found')
            return None

        try:
            y_vector = ncfile.variables[y_field][:]
        except KeyError:
            print('KeyError: y_field key not found')
            return None

        # Determine extents of input netCDF file

        n_cols = len(x_vector)
        n_rows = len(y_vector)
        # Be careful if coordinate system is lat-lon and southern
        # hemisphere, etc.
        # Should be in meters (projected coordinate system)
        dx = abs(x_vector[1] - x_vector[0])  # in meters
        dy = abs(y_vector[1] - y_vector[0])  # in meters

        # the nc_file uses center of cell coords
        # Change if not cell center coords
        x_ll = x_vector.min() - dx / 2
        y_ll = y_vector.min() - dy / 2

        extent = [x_ll, y_ll,
                  x_ll + (n_cols) * dx,
                  y_ll + (n_rows) * dy]

        if cellsize_return:
            extent += [dx, dy]

        ncfile.close()

    else:
        raise IOError("File type .{0} not recoginizeable for parsing extent"
                      "".format(file_type))

    return extent


def download_zipped_url(url, downloads):
    """
    Downloads a url that is expected to be a zipped folder.
    """
    r = requests.get(url, stream=True)
    if r.status_code == 404:
        out.error(
            "It appears the downloadable image no longer exists, please "
            "submit an issue at "
            "https://github.com/USDA-ARS-NWRC/basin_setup/issues.\nStatus"
            " 404 found on request from:\n{}".format(url))
        sys.exit()

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(downloads)


def convert_shapefile(fname, out_f):
    """
    Handles various shapefile filetype scenario and output a shapefile to out_f
    in the correct file format

    Args:
        fname: String file path

    """
    fname = abspath(expanduser(fname))

    if isfile(fname):
        name, ext = fname.split('.')
        out_dir = dirname(name)
        name = basename(name)

    else:
        raise IOError('File {0} does not exist')

    # Zipped KML file
    if ext == 'kmz':
        out.msg("KMZ (Compressed KML) file provided, unzipping...")
        # Copy to a zip
        zip_fname = join(out_dir, name + '.zip')
        copyfile(fname, zip_fname)

        zip_ref = zipfile.ZipFile(zip_fname, 'r')
        zip_ref.extractall(out_dir)
        zip_ref.close()
        os.remove(zip_fname)

        # Go find the .KML file
        out.msg("Searching for resulting KML...")
        for root, dirs, files in os.walk(out_dir):
            for f in files:
                if f.split('.')[-1] == 'kml':
                    fname = join(root, f)
                    ext = 'kml'
                    name = basename(fname)
                    out.respond('KML found!{0}'.format(fname))
                    break

    # For the mean time we need to do this until we figure out how to over come
    # converting from lat long to utm
    if ext != 'shp':
        raise IOError("Please use shapfiles")


def getWKT_PRJ(epsg_code):
    """
    Get the projection information for the points based on the EPSG code.
    Code copied and pasted from
    https://glenbambrick.com/2016/01/09/csv-to-shapefile-with-pyshp/
    """
    wkt = urllib.urlopen("http://spatialreference.org/ref/epsg/{0}"
                         "/prettywkt/".format(epsg_code))

    remove_spaces = wkt.read().replace(" ", "")
    output = remove_spaces.replace("\n", "")
    return output


def setup_and_check(required_dirs, basin_shapefile, dem, subbasins=None):
    """
    Check the arguments that were provided and provides some of the
    directory structure for the setup.

    Args:
        required_dirs: dictionary of directories to be used
        basin_shapefile: path to shape file of the basin outline
        dem: path to the dem that the shapefile would exist in.
        subbasins: optional list of subbasins to add subbasin filenames
                   should be in the format of desired name _ subbasin

    Return:
        images: dictionary of paths relevant to the final products.
    """

    # Filename and paths and potential sources
    images = {
        'dem': {
            'path': None,
            'source': None
        },
        'basin outline': {
            'path': None,
            'source': None,
            'epsg': None
        },
        'mask': {
            'path': None,
            'source': None,
            'short_name': 'mask'
        },
        'vegetation type': {
            'path': None,
            'source': None,
            'map': None,
            'short_name': 'veg_type'
        },
        'vegetation height': {
            'path': None,
            'source': None,
            'map': None,
            'short_name': 'veg_height'
        },
        'vegetation k': {
            'path': None,
            'source': None,
            'short_name': 'veg_k'
        },
        'vegetation tau': {
            'path': None,
            'source': None,
            'short_name': 'veg_tau'
        },
        'maxus': {
            'path': None,
            'source': None
        }
    }

    if is_float(dem):
        # Single float value provided
        images['dem']['path'] = float(dem)

    else:
        # Populate Images for non downloaded files\
        images['dem']['path'] = abspath(expanduser(dem))

    # Add in the subbasins
    if subbasins is not None:
        if not isinstance(subbasins, list):
            subbasins = [subbasins]

        for zz, sb in enumerate(subbasins):
            base = basename(sb).split('.')[0].lower()
            name = base.replace('_outline', '')
            name = name.replace('_subbasin', '')
            name = name.replace('  ', '')  # remove any double spaces
            name = name.replace('_', ' ')
            pth = abspath(expanduser(sb))
            # Capitalize the first letter
            name = proper_name(name)
            # Shapefiles
            images['{} subbasin'.format(name)] = \
                {'path': pth, 'source': None, 'epsg': None}
            # Images of masks
            images['{} mask'.format(name)] = \
                {'path': None, 'source': None, 'short_name': '{}'
                 ''.format(name + ' mask')}

    # Populate images for downloaded sources
    images['vegetation type']['source'] = \
        'https://landfire.cr.usgs.gov/bulk/downloadfile.php?FNAME=US_140_mosaic-US_140EVT_20180618.zip&TYPE=landfire'  # noqa

    images['vegetation height']['source'] = \
        'https://landfire.cr.usgs.gov/bulk/downloadfile.php?FNAME=US_140_mosaic-US_140EVH_20180618.zip&TYPE=landfire'  # noqa

    images['vegetation type']['path'] = \
        join(required_dirs['downloads'],
             'US_140EVT_20180618',
             'Grid', 'us_140evt',
             'hdr.adf')

    images['vegetation height']['path'] = \
        join(required_dirs['downloads'],
             'US_140EVH_20180618',
             'Grid',
             'us_140evh',
             'hdr.adf')

    # Make directories and create setup
    for k, d in required_dirs.items():
        full = abspath(expanduser(d))

        if not isdir(dirname(full)):
            raise IOError("Path to vegetation data/download directory does"
                          " not exist.\n %s" % full)

        if k != 'downloads':
            if isdir(full):
                out.warn("{0} folder exists, potential to overwrite"
                         " non-downloaded files!".format(k))

            else:
                out.msg("Making folder...")
                os.mkdir(full)
        else:
            if isdir(full):
                out.respond("{0} folder found!".format(k))
            else:
                out.msg("Making {0} folder...".format(k))
                os.mkdir(full)

    return images


def setup_point(images, point, cell_size, temp, pad, epsg_code):
    """
    Creates a shapefile that is exactly the 4 corners of a single point for
    making 'point' runs.

    Args:
        images: dictionary containing the image paths.
        point: a tuple containing x,y in utm
        cell_size: Pixel size
        temp: temporary folder for working files,
        pad: extra cells to keep for the point run
    """

    point = [float(p) for p in point.split(',')]

    # Check for asymetric padding request in a point model.

    if len(set(pad)) != 1:
        out.error("Asymetric padding is not allowed for point models!\npadding"
                  " = {}".format(pad))

    cell_size = int(cell_size)
    padding = cell_size * int(pad[0])
    points = []
    half_width = cell_size / 2
    x0 = point[0] - half_width - padding
    y0 = point[1] - half_width - padding
    x1 = point[0] + half_width + padding
    y1 = point[1] + half_width + padding
    points.append((x0, y0))  # Bottom left
    points.append((x0, y1))  # Upper left
    points.append((x1, y1))  # Upper Right
    points.append((x1, y0))  # Bottom Right

    # Write the points to a csv
    name = "points"
    SHP = join(temp, '{0}.shp'.format(name))
    PRJ = join(temp, '{0}.prj'.format(name))
    images['basin outline']['path'] = SHP

    point_shp = geometry.Polygon(points)
    shp_writer = shapefile.Writer()
    shp_writer.field("outline")

    converted_shape = shapely_to_pyshp(point_shp)
    shp_writer._shapes.append(converted_shape)
    shp_writer.record(["outline"])
    shp_writer.save(SHP)

    # Apply the EPSG code
    epsg = getWKT_PRJ(epsg_code)
    with open(PRJ, 'w') as f:
        f.write(epsg)
        f.close()

    return images


def check_shp_file(images, epsg=None, temp=None):
    """
    Require a shapefile and make a full path for either point or basin areas
    Args:
        images: dictionary containing paths and information on the images used
        epsg: Desired projection code
        temp: Work directory for temporary files
    Returns:
        images: a dictionary to modified paths for images in progress
    """
    out.dbg("Checking Basin Shapefile...")
    basin_shapefile = images['basin outline']['path']

    # Only accept .shp for now
    if basin_shapefile.split('.')[-1] != 'shp':
        images['basin outline']['path'] = \
            abspath(expanduser(basin_shapefile))

        fname = (basename(images['basin outline']['path'])).split('.')[0]
        images['basin outline']['path'] = join(temp, fname + '.shp')
        convert_shapefile(basin_shapefile, images['basin outline']['path'])

    else:
        images['basin outline']['path'] = \
            abspath(expanduser(basin_shapefile))

    # Loop through basins and check projections
    for bsn in [img_name for img_name in images.keys() if 'basin' in img_name]:

        # Reprojection requested
        if epsg is not None:
            out.msg("Reprojecting {} shapefile...".format(bsn))
            # Rename the resulting file
            newfile = basename(images[bsn]['path'])
            newfile = join(temp, newfile.split('.')[0] + "_epsg_{}.shp"
                           "".format(epsg))
            cmd_args = ['ogr2ogr', '-t_srs', 'EPSG:{}'.format(epsg), newfile,
                        images[bsn]['path']]
            s = check_output(cmd_args, universal_newlines=True)
            out.dbg(s)
            images[bsn]['path'] = newfile
            images[bsn]['epsg'] = epsg

        else:
            out.msg("Attempting to determine the EPSG value of {} shapefile..."
                    "".format(bsn))
            basin_shp_info = check_output(['ogrinfo', '-al',
                                           images[bsn]['path']],
                                          universal_newlines=True)
            out.dbg(basin_shp_info)

            basin_info = basin_shp_info.split('\n')
            epsg_info = [auth for auth in basin_info if "epsg" in auth.lower()]
            epsg = strip_chars(epsg_info[-1].split(',')[-1])
            out.respond("EPSG = {}".format(epsg))
            images[bsn]['epsg'] = epsg

    return images


def check_and_download(images, required_dirs):
    """
    Checks for veg type and height data

    args:
        images: dictionary containing sources, filenames, and other attributes
        required_dirs: dictionary of directories that are required

    returns:
        images: a modified dictionary of the original dicitonary
    """
    out.dbg("Checking file paths and downloads...")
    for image_name in ['vegetation type', 'vegetation height']:
        info = images[image_name]
        info['path'] = abspath(expanduser(info['path']))
        images[image_name] = info

        out.msg("Checking for {0} data in:\n\t{1}".format(
            image_name,
            required_dirs['downloads']))

        # Cycle through all the downloads
        out.msg("Looking for: \n%s " % info['path'])
        if not isdir(dirname(info['path'])):

            # Missing downloaded data
            out.msg("Unzipped folder not found, check for zipped folder.")
            zipped = (dirname(dirname(dirname(info['path']))) + '.zip')
            out.msg("Looking for:\n %s" % zipped)

            if not isfile(zipped):
                # Zip file does not exist
                out.warn("No data found!\nDownloading {} ...".format(image_name))  # noqa
                out.warn("This could take up to 20mins, so sit back and relax.")  # noqa
                download_zipped_url(info['source'], required_dirs['downloads'])

            # Downloaded but not unzipped
            else:
                out.respond("Zipped data found, unzipping...")
                z = zipfile.ZipFile(zipped)
                z.extractall(zipped)
            # Download found as expected
        else:
            out.respond("found!")

        # CSV map should be in the downloaded folder name
        map_src = dirname(dirname(dirname(info['path'])))

        out.msg("Searching for {0} map...".format(image_name))

        for root, dirnames, filenames in os.walk(map_src):
            for f in filenames:
                # Looking for the only csv
                if f.split('.')[-1] == 'csv':
                    info['map'] = join(root, f)
                    out.respond('{0} map found!\n\t{1}'.format(image_name,
                                                               info['map']))
                    break

        if info['map'] is None:
            out.error("Could not find {0} map!".format(image_name))
            sys.exit()
    return images


def process(images, TEMP, cell_size, pad=None, extents=None, epsg=None):
    """
    Creates the mask image, veg_type, height and dem images,
    reprojects them to the proejction of the basin_shapefile and converts them
    to individual netcdf files

    Args:
        images: dictionary containing paths for each image
        TEMP: temporary work dir
        cell_size: Desired cell size for the images.
        pad: list of number of cells to add to an image from the extent of the
             shapefile, format = [ LEFT, BOTTOM, RIGHT, TOP]
        extents: list of of coordinates in the shapefiles projection,
                 format = [ LEFT, BOTTOM, RIGHT, TOP]

    Returns:
        images: dictionary containing the path to the latest image for
            each key.
        extents: The list of the bottom left and upper right image extents plus
                padding or whatever was requested specifically.
    """

    cell_size = int(cell_size)
    # Gather general info for basin shape file
    out.msg("Retrieving basin outline info...\n")

    # No explicit
    if extents is None:
        extents = parse_extent(images['basin outline']['path'])

        padding = [cell_size * int(p) for p in pad]

        # Pad the extents
        padded_extent = []
        extents = [float(e) for e in extents]

        # Allows for custom padding
        padded_extent.append(extents[0] - padding[0])  # Left
        padded_extent.append(extents[1] - padding[1])  # Bottom
        padded_extent.append(extents[2] + padding[2])  # Right
        padded_extent.append(extents[3] + padding[3])  # Top

        # Check cell size fits evenly in extent range
        extents = padded_extent
        extents = condition_extent(extents, cell_size)

    else:
        extents = [float(e) for e in extents]

    s_extent = [str(e) for e in extents]

    # Recover projection info
    proj = images['basin outline']['path'].split('.')[0] + '.prj'

    # Process all the masks
    for msk in [k for k in images.keys() if 'mask' in k]:

        # Create a tif of the mask from shapefile then convert to netcdf
        fnm = msk.replace(' ', '_')

        # Basin wide mask
        if msk == 'mask':
            shp_nm = 'basin outline'
        else:
            shp_nm = msk.split('mask')[0] + "subbasin"

        images[msk]['path'] = join(TEMP, '{}.tif'.format(fnm))

        # clips, sets resolution
        z = Popen(['gdal_rasterize', '-tr', str(cell_size), str(cell_size),
                   '-te', s_extent[0], s_extent[1], s_extent[2], s_extent[3],
                   '-burn', '1', '-ot', 'int', images[shp_nm]['path'],
                   images[msk]['path']], stdout=PIPE)
        z.wait()

        # Convert the mask to netcdf
        NC = abspath(join(TEMP,
                          'clipped_{}.nc'.format(msk.replace(' ', '_'))))
        s = Popen(['gdal_translate', '-of', 'NETCDF', '-sds',
                   images[msk]['path'], NC], stdout=PIPE)
        s.wait()

        images[msk]['path'] = NC

    # Get the final extent
    extents = parse_extent(images["mask"]['path'])
    s_extent = [str(e) for e in extents]

    # If user passes an float then don't process the image, were probably
    # using a point model

    if is_float(images['dem']['path']):
        process_names = ['vegetation height', 'vegetation type']
    else:
        process_names = ['vegetation height', 'vegetation type', 'dem']

    # Reproject and clip according to the basin mask
    for name in process_names:
        img = images[name]

        # Get data loaded in
        out.msg("Getting {0} image info...".format(name))

        check_output(['gdalinfo', img['path']], universal_newlines=True)

        fname = name.replace(' ', '_')

        CLIPPED = abspath(join(TEMP, 'clipped_{0}.tif'
                               ''.format(fname)))
        if name == "vegetation type":
            resample = "near"
        else:
            resample = "bilinear"

        out.msg("Reprojecting and clipping {0} rasters...".format(name))

        cmd = ['gdalwarp',
               '-t_srs', proj,
               '-te', s_extent[0], s_extent[1], s_extent[2], s_extent[3],
               '-tr', str(cell_size), str(cell_size),
               '-r', resample,
               '-overwrite',
               img['path'], CLIPPED]

        p = Popen(cmd, stdout=PIPE)
        p.wait()

        # Convert to Netcdf
        out.msg("Converting {0} to NetCDF...".format(name))
        NC = CLIPPED.split('.')[0] + '.nc'
        s = Popen(['gdal_translate', '-of', 'NETCDF', '-sds', CLIPPED, NC],
                  stdout=PIPE)
        images[name]['path'] = NC
        s.wait()

    return images, extents


def create_netcdf(images, extent, cell_size, output_dir, basin_name='Mask'):
    """
    Create the initial netcdf and then writes the all images

    Args:
        images: dictionary containing the latest paths to various images
        extent: The final extent required
        output_dir: Output location for results
        basin_name: Name for the basin


    Returns:
        topo: a netcdf dataset object populated with necessary variables
    """
    # Building the final netcdf
    out.msg("\nCreating final output for netcdf...")

    # Setup the extent using the files we just generated. The extent is decided
    # oddly in gdal so it was tough to generate the extents manually, this way
    # we let gdal manage it.

    ds = Dataset(images["mask"]['path'])
    x = ds.variables['x'][:]
    y = ds.variables['y'][:]
    ds.close()
    extent = [float(e) for e in extent]
    # x = np.arange(extent[0], extent[2], int(cell_size))
    # y = np.arange(extent[1], extent[3], int(cell_size))

    out.respond("Output Netcdf setup is:\n\t {0} x {1} pixels"
                "\n\t {2} x {3} meters"
                "\n\t Bottom Left Coordinates {4}, {5}"
                "\n\t Upper Right Coordinates {6}, {7}"
                "\n\t Resolution {8}m\n".format(x.shape[0],
                                                y.shape[0],
                                                extent[2] - extent[0],
                                                extent[3] - extent[1],
                                                extent[0],
                                                extent[1],
                                                extent[2],
                                                extent[3],
                                                cell_size))

    TOPO_PATH = join(output_dir, 'topo.nc')
    topo = Dataset(TOPO_PATH, 'w', format='NETCDF4', clobber=True)

    # Add modification note
    h = '[{}] Data added or updated'.format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    setattr(topo, 'last_modified', h)

    # Add dimensions, variables and such
    topo.createDimension('y', y.shape[0])
    topo.createDimension('x', x.shape[0])

    topo.createVariable('y', 'f4', 'y', zlib=True, least_significant_digit=3)
    topo.createVariable('x', 'f4', 'x', zlib=True, least_significant_digit=3)

    # The y variable attributes
    topo.variables['y'][:] = y

    topo.variables['y'].setncattr(
        'units',
        'meters')
    topo.variables['y'].setncattr(
        'description',
        'UTM, north south')
    topo.variables['y'].setncattr(
        'long_name',
        'y coordinate')

    # The x variable attributes
    topo.variables['x'][:] = x
    topo.variables['x'].setncattr(
        'units',
        'meters')
    topo.variables['x'].setncattr(
        'description',
        'UTM, east west')
    topo.variables['x'].setncattr(
        'long_name',
        'x coordinate')

    # Cycle through and add/generate all the images that go into the topo.nc
    topo_names = [
        k for k in images.keys() if (
            'basin' not in k and k != 'maxus')]

    # Add in topo variables
    for name, image in images.items():
        precision = 3

        if name in topo_names:

            if 'short_name' in image.keys():
                short_name = image['short_name']
            else:
                short_name = name

            long_name = name

            # Data reduction and names
            if 'mask' in short_name:
                dtype = 'u1'  # U-BYTE
                if short_name == 'mask':
                    if short_name == 'mask':
                        if basin_name is None:
                            long_name = 'Full Basin'
                        else:
                            long_name = proper_name(basin_name)
                else:
                    long_name = name.replace(' mask', '')

            elif short_name in ['veg_type']:
                dtype = 'u2'  # U-INT 16 bit

            else:
                dtype = 'f4'  # Floating point 32
                if short_name in ["veg_k", "veg_tau"]:
                    precision = 4

            out.respond("Adding {0}, type={1}".format(name, dtype))
            topo.createVariable(short_name, dtype, ('y', 'x'), zlib=True,
                                least_significant_digit=precision)
            topo.variables[short_name].setncattr('long_name', long_name)

            if is_float(image['path']):
                topo.variables[short_name][:] = image['path']

            # paths
            elif image['path'] is not None and isfile(image['path']):
                d = Dataset(image['path'], 'r')
                try:
                    topo.variables[short_name][:] = d.variables['Band1'][:]

                except Exception as e:
                    out.error(
                        "Error assigning {} to netcdf.".format(short_name))

                    if short_name == 'dem':
                        out.error("Size of {} is {} versus size of final topo"
                                  " netcdf which is {}".format(
                                      short_name,
                                      d.variables['Band1'][:].shape,
                                      topo.variables[short_name][:].shape))

                        out.msg(
                            "{}\n\nHint: This maybe caused by the default"
                            " padding creating extents bigger than the"
                            " original DEM image. \nTry decreasing the padding"
                            "  using the --pad or -pd flag.\n".format(str(e)))
                        sys.exit()

                    elif 'mask' in short_name:
                        out.error(
                            "Size of {} is {} versus size of final topo"
                            " netcdf which is {}".format(
                                short_name,
                                d.variables['Band1'][:].shape,
                                topo.variables[short_name][:].shape))
                    else:
                        raise(e)

                d.close()

    # Define some global attributes
    fmt = '%Y-%m-%d %H:%M:%S'
    topo.setncattr_string('Conventions', 'CF-1.6')
    topo.setncattr_string('dateCreated', datetime.now().strftime(fmt))
    topo.setncattr_string('Title', 'Topographic Images for SMRF/AWSM')
    topo.setncattr_string(
        'history',
        '[{}] Create netCDF4 file using Basin Setup v{}'.format(
            datetime.now().strftime(fmt),
            __version__)
    )
    topo.setncattr_string(
        'institution',
        'USDA Agricultural Research Service, Northwest Watershed Research'
        ' Center')
    topo.setncattr_string(
        'generation_command',
        '{}'.format(
            " ".join(
                sys.argv)))

    return topo


def calculate_height_tau_k(topo, images, height_method='average',
                           veg_params=None, bypass_veg_check=False):
    """
    Calculates the images for veg height, veg tau and veg K and adds them  to
    the netcdf.

    Args:
        topo: NetCDF Dataset object containing variables for veg_height,
            veg_tau, and veg_k
        images: dictionary containing the paths for each image
        height_method: Determines the way veg_height is calculated given the
                       veg height data. Each method is using the range
                       provided. Options are average, max, randomized
        veg_params: path to another interpretation of the vegetation radiation
                    parameters
        bypass_veg_check: Flag to skip the error in the event a veg parameter
            is missing.
    """

    out.msg('Calculating veg_tau and veg_k...')

    # Open veg type data set to create empty vars to populate
    d = Dataset(images['vegetation type']['path'], 'r')

    veggies = np.array(d.variables['Band1'][:])
    veg_tau = np.zeros(veggies.shape)
    veg_tau.fill(np.NaN)

    veg_k = np.zeros(veggies.shape)
    veg_k.fill(np.NaN)

    # Get the unique values available in the array
    veg_values = np.unique(np.array(topo.variables['veg_type'][:]))
    d.close()

    # Open the key provided by Landfire to assign values in Tau and K
    vm = pd.read_csv(images['vegetation type']['map'])
    ind = vm['VALUE'].isin(veg_values)
    veg_map = vm.loc[ind, vm.columns]

    # We have a CSV describing the vegetation data
    if veg_params is not None:
        out.warn("Using the CSV file with vegetation parameters to define veg "
                 "tau and veg k")
        if not isfile(veg_params):
            out.error("Vegetation parameters CSV file {} does not exist"
                      "".format(veg_params))
            sys.exit()

        df_veg = pd.read_csv(veg_params, index_col="veg")

        # Determine underdefined values
        missing = [int(value)
                   for value in veg_values if int(value) not in df_veg.index]

        if missing and not bypass_veg_check:
            err = ("Vegetation Parameter file {} missing classes {}"
                   "").format(veg_params, ", ".join([str(v) for v in missing]))
            out.error(err)
            out.warn(
                "To accept missing data in the tau/K layers use"
                " '--bypass_veg_check'")
            raise IOError(err)

        # Cycle through values and assign them
        for value in veg_values:
            if value in df_veg.index:
                veg_tau[veggies == value] = df_veg['tau'].loc[value]
                veg_k[veggies == value] = df_veg['k'].loc[value]
            else:
                out.error(
                    "Bypassing not assigning any tau/k values for veg parameter {}".format(value))  # noqa

    # use the keywords and dictionaries to guess at the tau and K
    else:
        out.warn("Assuming Veg K and Tau values using keywords"
                 " found in veg data set")
        # Vegetation Tau and K table from Link and Marks 1999
        # http://onlinelibrary.wiley.com/doi/10.1002/(SICI)1099-1085(199910)13:14/15%3C2439::AID-HYP866%3E3.0.CO;2-1/abstract # noqa
        tau = {
            'open': 1.0,
            'deciduous': 0.44,
            'mixed conifer and deciduous': 0.30,
            'medium conifer': 0.20,
            'dense conifer': 0.16
        }
        mu = {
            'open': 0.0,
            'deciduous': 0.025,
            'mixed conifer and deciduous': 0.033,
            'medium conifer': 0.040,
            'dense conifer': 0.074
        }

        # Keywords for landfire data sets
        veg_keywords = {
            'open': ['Sparsely vegetated', 'graminoid'],
            'deciduous': ['Deciduous open tree canopy'],
            'mixed conifer and deciduous': ['Mixed evergreen-deciduous shrubland'],  # noqa
            'medium conifer': ['Mixed evergreen-deciduous open tree canopy'],
            'dense conifer': ['Evergreen closed tree canopy', 'conifer']
        }

        # Cycle through the key words in the table used for conversion/assign
        # values
        for k, keywords in veg_keywords.items():
            for word in keywords:
                veg_filter = veg_map['VALUE'].ix[veg_map['EVT_SBCLS'] == word]
                for vtype in veg_filter.tolist():
                    veg_tau[veggies == vtype] = tau[k]
                    veg_k[veggies == vtype] = mu[k]

    topo.variables['veg_tau'][:] = veg_tau
    topo.variables['veg_k'][:] = veg_k

    # Remap Vegetation Height
    out.msg('Estimating vegetation heights...')

    # Open veg heights and convert to array
    d = Dataset(images['vegetation height']['path'], 'r')
    veg_height = np.array(d.variables['Band1'][:])
    final_veg_height = np.zeros(veg_height.shape)

    height_values = np.unique(np.array(topo.variables['veg_height'][:]))
    d.close()

    # Open the key provided by Landfire to assign values in final veg height
    f = images['vegetation height']['map']
    height_key = pd.read_csv(f)
    height_key_unique = height_key[height_key['VALUE'].isin(height_values)]
    height_map = {}

    veg_map['HEIGHT'] = [np.NaN for i in range(len(veg_map.index))]

    # Parse the veg height ranges and create a dictionary for converting
    for i, row in height_key_unique.iterrows():
        description = row['CLASSNAMES']
        height_range = []
        for word in description.split(' '):

            # Attempt to provide a value if it converts
            try:
                height_range.append(float(word))
            except BaseException:

                # Exceptions to veg heights not provided with a height
                if description in ['Sparse Vegetation Height',
                                   'NASS-Row Crop',
                                   ' NASS-Close Grown Crop']:
                    height_range = [0, 0.1]
                elif description in ['Developed-Upland Deciduous Forest',
                                     'Developed-Upland Mixed Forest',
                                     'Developed - Medium Intensity']:
                    height_range = [0, 5]

                elif description in ['Developed-Upland Shrubland',
                                     'NASS-Vineyard']:
                    height_range = [0, 2]

                elif description in ['Developed-Upland Herbaceous',
                                     'NASS-Wheat']:
                    height_range = [0, 1]

        height_map[row['VALUE']] = height_range

    # Reassign height values using random, averaging or maximum
    for k, height in height_map.items():
        ind = veg_height == k
        if height_method == 'randomized':
            rand = np.random.rand(*veg_height[ind].shape)
            final_veg_height[ind] = (rand * height[1]) + height[0]

        elif height_method == 'max':
            final_veg_height[ind] = max(height)

        # Avg
        elif height_method == 'average':
            if len(height) == 2:
                final_veg_height[ind] = np.mean(height)
                try:
                    ind = veg_map['EVT_GP'] == k
                    veg_map.loc[ind, 'HEIGHT'] = np.mean(height)

                except Exception as e:
                    out.error(str(e))
                    out.error("Entry not found {0} in veg map!".format(k))
        else:
            raise ValueError("Height method not recognized. please use max,"
                             " randomized,or average")

    # Reassign to the NetCDF and finish
    topo.variables['veg_height'][:] = final_veg_height

    # Output a map for SMRF/AWSM USERS
    out.msg("Outputting a list of unique vegetation types...")
    veg_map = veg_map.sort_values(by='HEIGHT')
    output_dir = dirname(topo.filepath(encoding='utf-8'))
    veg_map[['VALUE', 'HEIGHT', 'CLASSNAME']].to_csv(
        join(output_dir, 'veg_map.csv'))

    # Output Veg Info
    return topo


def make_hill(topo, dem_var='dem', lower=1.0):
    """
    Modifies the dem by lowering the area around point models by the amount set
    in lower.

    Args:
        topo: Open Netcdf dataset containing the dem_var
        dem_var: The name of the dem variable in the dataset.
        lower: The amount in meters to lower the surround area.
    Returns:
        topo: An open Netcdf after being modified.
    """

    x_mid = int(len(topo.variables[dem_var][:, 0]) / 2)
    y_mid = int(len(topo.variables[dem_var][0, :]) / 2)
    out.warn("Creating a hill like 'point model' by lowering the surrounding"
             " area by {0}m".format(lower))
    removal = lower * np.ones(np.shape(topo.variables[dem_var]))
    removal[y_mid, x_mid] = 0
    topo.variables[dem_var][:] = topo.variables[dem_var][:] - removal

    return topo


def make_uniform(topo, approach='middle', hill=False):
    """
    Takes a data set and recalculates the values based on the approach.
    Particularly useful for setting up point models

    Args:
        topo: An existing netcdf dataset object with variables.
        approach: Specifies options for make values uniform options:
                  middle, average, max, min.
        hill: For point models lower all cells except center by 1mm

    Return:
        topo: modified netcdf dataset with uniform data

    """
    x_mid = int(len(topo.variables['dem'][:, 0]) / 2)
    y_mid = int(len(topo.variables['dem'][0, :]) / 2)

    for var in topo.variables:

        if var not in ['x', 'y', 'mask']:
            values = topo.variables[var][:]

            if approach == 'middle':
                value = values[y_mid, x_mid]

            elif approach == 'average':
                value = np.average(values)

            elif approach == 'min':
                value = np.min(values)

            elif approach == 'max':
                value = np.max(values)

            else:
                raise ValueError("{0} not an accetable option, options are "
                                 "middle, average, min, and max")

            topo.variables[var][:] = value

    return topo


def flip_image(topo):
    """
    Flips the image data over the x-axis and flips the y data

    Args:
        topo: open netcdf dataset with all the variables
    Returns:
        topo: an open netcdf dataset with flipped image
    """
    for var in topo.variables:
        if var not in ['x', 'projection']:
            topo.variables[var][:] = np.flipud(topo.variables[var][:])
    return topo


def main():

    # Parge command line arguments
    p = argparse.ArgumentParser(
        description='Setup a new basin for SMRF/AWSM.'
        ' Creates all the required static files'
        ' required for running a basin. The output is a'
        ' topo.nc containing: dem, mask, veg height,'
        ' veg type, veg tau, and veg k')

    p.add_argument('-f',
                   '--basin_shapefile',
                   dest='basin_shapefile',
                   required=False,
                   help="Path to shapefile that defines the basin in UTM "
                   " projection")

    p.add_argument('-c',
                   '--cell_size',
                   dest='cell_size',
                   required=False,
                   default=50,
                   help="Pixel size to use for the basin in meters,"
                   " Default: 50m")

    p.add_argument('-dm',
                   '--dem',
                   dest='dem',
                   required=True,
                   help="Digital elevation map file in geotiff or a single "
                   " value for point models")

    p.add_argument('-d',
                   '--download',
                   dest='download',
                   required=False,
                   default='~/Downloads',
                   help="Location to check for veg data or download vegetation"
                   " data, default: ~/Downloads")

    p.add_argument('-o',
                   '--output',
                   dest='output',
                   required=False,
                   default='./basin_setup',
                   help="Location to output data")

    p.add_argument('-p',
                   '--point',
                   dest='point',
                   required=False,
                   default=None,
                   help='Center of location to setup "point" model')

    p.add_argument('-pd',
                   '--pad',
                   dest='pad',
                   required=False,
                   default=5,
                   help="Number of cells to add on to the domain from the"
                   " extents of the basin shapfile, default: 5")

    p.add_argument('-apd',
                   '--asym_pad',
                   dest='apad',
                   nargs=4,
                   required=False,
                   help="Number of cells to add on to the domain for each"
                   " side. Format is [Left, Bottom, Right, Top]")

    p.add_argument('-u',
                   '--uniform',
                   dest='uniform',
                   action='store_true',
                   help="Specifies whether for point runs to use a uniform"
                   "elevation and veg values in the 'point' domain")

    p.add_argument('-e',
                   '--epsg',
                   dest='epsg',
                   help="epsg code for the point run, see "
                   "http://spatialreference.org/ref/epsg/ for options")

    p.add_argument('-dbg',
                   '--debug',
                   dest='debug',
                   action='store_true',
                   help="Debug flag prints out more info and doesn't delete"
                   " the working folder")

    p.add_argument('-hl',
                   '--hill',
                   dest='hill',
                   action='store_true',
                   help='For point models drops all cells except the center'
                   'cell by 1mm')

    p.add_argument('-fl',
                   '--noflip',
                   dest='noflip',
                   action='store_true',
                   help='Do not flip arrays across the x axis')

    p.add_argument('-sb',
                   '--subbasins',
                   dest='subbasins',
                   nargs='+',
                   help='provide a file list of subassin '
                   'shapefiles you want to be added as'
                   ' masks')

    p.add_argument('-bn',
                   '--basin_name',
                   dest='basin_name',
                   nargs='+',
                   help='provide a long name for the basin'
                   ' total mask')

    p.add_argument('-vc',
                   '--veg_params',
                   dest='veg_params',
                   default=None,
                   help=('Provide a csv defining veg tau and veg'
                         'k values for the available vegetation'
                         ' classes, any veg classes found in the '
                         ' topo not listed in the csv will throw '
                         ' an error'))

    p.add_argument('-bp',
                   '--bypass_veg_check',
                   dest='bypass_veg_check',
                   action='store_true',
                   help='Allows the user to bypass error raised when the tau/k'
                   ' layers are missing data. For research purposes only.')

    p.add_argument('-ex',
                   '--extents',
                   dest='desired_extents',
                   nargs=4,
                   required=False,
                   help="Number of cells to add on to the domain for each"
                   " side. Format is [Left, Bottom, Right, Top]")

    args = p.parse_args()

    # Global debug variable
    global DEBUG
    DEBUG = args.debug

    # Print a nice header
    msg = "Basin Setup Tool v{0}".format(__version__)
    m = "=" * (2 * len(msg) + 1)
    out.msg(m, 'header')
    out.msg(msg, 'header')
    out.msg(m, 'header')

    # ===========================================================================
    # Check Inputs/ Setup
    # ===========================================================================

    # Check and setup for an output dir, downloads dir, and temp dir
    required_dirs = {'output': abspath(expanduser(args.output)),
                     'downloads': abspath(expanduser(args.download)),
                     'temp': abspath(expanduser(join(args.output, 'temp')))}

    TEMP = required_dirs['temp']
    images = setup_and_check(required_dirs, args.basin_shapefile, args.dem,
                             subbasins=args.subbasins)

    if args.desired_extents is not None:
        out.warn("Using --extents will override any padding requested!")
        pad = None
    else:
        # DEM Cell padding
        pad = int(args.pad)

        # No asymetric padding provided
        if args.apad is None:
            pad = [pad for i in range(4)]
        else:
            pad = [int(i) for i in args.apad]

    # --------- OPTIONAL POINT MODEL SETUP ---------- #
    if args.point is not None:
        out.msg("Point model setup requested!")
        images = setup_point(images, args.point, args.cell_size, TEMP, pad,
                             args.epsg)
        # For point setup the only padding should be around the center pixel
        pad = 0
    else:
        images['basin outline']['path'] = \
            abspath(expanduser(args.basin_shapefile))

    images = check_shp_file(images, epsg=args.epsg, temp=TEMP)

    # ===========================================================================
    # Downloads and Checking
    # ===========================================================================
    images = check_and_download(images, required_dirs)

    # ===========================================================================
    # Processing
    # ===========================================================================
    images, extents = process(images, TEMP, args.cell_size, pad=pad,
                              extents=args.desired_extents)

    # ===========================================================================
    # Post Processing
    # ===========================================================================
    if args.basin_name is not None:
        basin_name = " ".join(args.basin_name)
    else:
        basin_name = None

    topo = create_netcdf(images, extents, args.cell_size,
                         required_dirs['output'], basin_name)
    # Calculates TAU and K
    if args.veg_params is None:
        veg_params = __veg_parameters__
    else:
        veg_params = args.veg_params
    topo = calculate_height_tau_k(topo, images, veg_params=veg_params,
                                  bypass_veg_check=args.bypass_veg_check)

    # Add the projection information
    topo = add_proj(
        topo,
        images['basin outline']['epsg'],
        images['dem']['path'])

    # Making a point
    if args.point is not None:
        if args.uniform:
            out.warn("Using uniform flag, all outputted values will the be"
                     " equal to the center pixel")

            topo = make_uniform(topo, approach='middle')

        if args.hill:
            topo = make_hill(topo, dem_var='dem')

    # Don't Flip the image over the x axis if it is not requested
    if not args.noflip:
        out.msg("Flipping images...")
        topo = flip_image(topo)

    topo.close()

    out.msg('\nRequested output written to:')
    out.respond('{0}'.format(join(required_dirs['output'], 'topo.nc')))
    out.msg("Basin setup files complete!\n")

    # Don't Clean up if we are debugging so we can look at the steps
    if not DEBUG:
        out.msg('Cleaning up temporary files.')
        rmtree(required_dirs['temp'])


if __name__ == '__main__':
    main()
