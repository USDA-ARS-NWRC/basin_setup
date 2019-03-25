#!/usr/bin/env python3

import argparse
import numpy as np
import os
from subprocess import check_output
import sys
import time
import datetime
import shutil
import coloredlogs
import netCDF4 as nc
from spatialnc.topo import get_topo_stats
from spatialnc.utilities import copy_nc, mask_nc
import logging
from inicheck.utilities import mk_lst, remove_chars
import pandas as pd


DEBUG=False
BASIN_SETUP_VERSION = '0.8.2'


def parse_fname_date(fname):
    """
    Attempts to parse the date from the filename
    """
    bname = os.path.basename(fname)
    if "_" in bname:
        bname = bname.split("_")[0]

    # Only grab the numbers in the basename
    str_dt = "".join([c for c in bname if c.isnumeric()])
    dt = pd.to_datetime(str_dt)

    return dt


def parse_gdalinfo(fname):
    """
    Executes gdalinfo from the commandline on fname. Returns a dictionary of
    cell size, origin, and extents
    """

    image_info = {}
    info = check_output(["gdalinfo",fname], universal_newlines=True)
    for line in info.split("\n"):
        if "=" in line:
            data = line.split("=")
            data = [k.strip().lower() for k in data]

            # Keyword should always be first
            if data[0] in ["pixel size", "origin"]:

                result = []

                if "," in data[1]:
                    v = data[1].split(',')
                else:
                    v = [data[1]]

                for s in v:
                    result.append(float(remove_chars(s,"()\n:")))

                image_info[data[0]] = mk_lst(result, unlst=True)

    return image_info


class GRM(object):

    def __init__(self,**kwargs):

        # check kwargs
        for k,v in kwargs.items():
            setattr(self, k, v)

        # Setup external logging if need be
        if not hasattr(self,'log'):
            self.log = logging.getLogger(__name__)

        # Manage Logging
        level="INFO"

        if hasattr(self, 'debug'):
            if self.debug:
                level='DEBUG'
            else:
                self.debug = False

        # Assign some colors and formats
        coloredlogs.install(fmt='%(levelname)-5s %(message)s', level=level,
                                                               logger=self.log)
        self.log.info("Getting Topo attributes...")
        self.ts = get_topo_stats(self.topo)
        self.log.info("Using topo cell size which is {} {}"
                                                  "".format(
                                                        abs(int(self.ts['du'])),
                                                        self.ts['units']))
        # Get aso super depth info
        self.image_info = parse_gdalinfo(self.image)

        # Titling
        renames = {"brb":"boise river basin",
                   "lakes":"mammoth lakes basin"}

        if self.basin in renames.keys():
            self.basin = renames[self.basin]
        else:
            self.basin = "{} river basin".format(self.basin)
        self.basin = self.basin.title()

        self.log.info("Working on the {}".format(self.basin))

    def handle_error(self, dbgmsg, errmsg, error=False):
        """
        Manages the error produced by our checks.
        """
        if error:
            self.log.error(errmsg)
            raise ValueError(errmsg)
        else:
            self.log.debug(dbgmsg)

    def grid_match(self):
        """
        Interpolates the newly scaled grid to the current grid
        """

        outfile = os.path.basename(self.image)

        self.log.info("Rescaling image raster from {} to {}"
                    "".format(int(self.image_info['pixel size'][0]),
                              abs(int(self.ts['du']))))



        outfile, ext = outfile.split(".")
        outfile = outfile + ".nc"

        outfile = os.path.join(self.temp, outfile)

        self.log.debug("Writing grid adjusted image to:\n{}".format(outfile))
        cmd = ["gdalwarp",
               "-r bilinear",
               "-of NETCDF",
               "-overwrite",
               "-dstnodata nan",
               "-te {} {} {} {}".format(int(np.min(self.ts["x"])),
                                        int(np.min(self.ts["y"])),
                                        int(np.max(self.ts["x"])),
                                        int(np.max(self.ts["y"]))),
               "-ts {} {}".format(self.ts['nx'], self.ts['ny']),
               self.image,
               outfile]

        self.log.debug("Executing: {}".format(" ".join(cmd)))
        s = check_output(" ".join(cmd), shell=True)

        self.working_file = outfile

    def create_lidar_netcdf(self):
        """
        Creates a new lidar netcdf to contain all the flights for one water year.
        """

        self.log.info("Output NetCDF does not exist, creating a new one!")

        # Exclude all variables except dimensions
        ex_var = [v for v in self.topo_ds.variables if v.lower() not in ['x','y','projection']]

        # Copy a topo like netcdf image to add depths to
        self.ds = copy_nc(self.topo, self.outfile, exclude=ex_var)
        self.ds.createDimension("time", None)

        start_date = pd.to_datetime("{}-10-01".format(self.start_yr))
        self.log.debug("Using {} as start of water year for stamping netcdf"
        "".format(start_date.isoformat()))

        # Assign time and count days since 10-1
        times = self.ds.createVariable('time', 'f', ('time'))
        setattr(self.ds.variables['time'], 'units', 'hours since %s' % start_date)
        setattr(self.ds.variables['time'], 'calendar', 'standard')

        # Add append a new image
        self.ds.createVariable("depth", "f", ("time", "y", "x"),
                                        chunksizes=(6, 10, 10), fill_value=np.nan)

        self.ds['depth'].setncatts({"units":"meters",
                                "long_name":"lidar sself.now depths",
                                "short_name":'depth',
                                "grid_mapping":"projection",
                                "description":"Measured snow depth from ASO"
                                              " lidar."})

        # Adjust global attributes
        self.ds.setncatts({"last_modified":self.now,
                    "dateCreated":self.now,
                    "Title":"ASO 50m Lidar Flights Over the {} for Water Year {}."
                            "".format(self.basin, self.water_year),
                    "history":"Created using Basin Setup v{}"
                              "".format(BASIN_SETUP_VERSION),
                    })

        # Attribute gets copied over from the topo
        self.ds.delncattr("generation_command")

    def add_to_collection(self):
        """
        Adds a new netcdf to an existing one that includes all the metadata.
        If the existing file doesn't actually exist, it will create one.
        """

        # Grab a human readable timefor today
        self.now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not hasattr(self, "date"):
            self.date = parse_fname_date(self.image)

        else:
            self.date = pd.to_datetime(self.date)

        # Calculate the start of the water year and the water year
        self.water_year = self.date.year

        if self.date.month <= 10:
            self.start_yr = self.water_year - 1
        else:
            self.water_year += 1

        # output netcdf
        self.outfile = os.path.join(self.output, "lidar_depths_wy{}.nc"
                                                 "".format(self.water_year))
        self.log.info("Lidar Flight for {}".format(
                                           self.date.isoformat().split('T')[0]))

        if not hasattr(self, "epsg"):
            pass

        # Open the topo for gathering data from
        self.topo_ds = nc.Dataset(self.topo, mode='r')


        # Prexisting collection of lidar in netcdf found
        if  os.path.isfile(self.outfile):
            self.log.info("Output NetCDF exists, checking to see if everything matches.")

            # Retrieve existing dataset
            self.ds = nc.Dataset(self.outfile, mode='a')

            # Check for matching basins
            self.check_basin_match()

            # Check for matching water years
            self.check_water_year_match()

            # Check to see if we are about to overwrite data
            self.check_overwrite()

            # Check the basin mask in the topo matches for the dataset
            self.check_topo_match()

        # Create a netcdf
        else:
            self.create_lidar_netcdf()

        # Calculate the time index
        index = self.get_time_index()

        # Update the modified attribute
        self.ds.setncatts({"last_modified":self.now})

        # Open the newly convert depth and add it to the collection
        self.log.info("Extracting the new netcdf data...")
        new_ds = nc.Dataset(self.working_file, mode='a')

        # Fill values to np.nan
        idx = new_ds.variables['Band1'][:] == \
                                            new_ds.variables['Band1']._FillValue
        new_ds.variables['Band1'][:][idx] = np.nan

        new_ds.variables['Band1'][:] = np.flipud(new_ds.variables['Band1'][:])

        new_ds.close()

        # Mask it
        self.log.info("Masking lidar data...")
        new_ds = mask_nc(self.working_file, self.topo, output=self.temp)

        depths = new_ds.variables['Band1'][:]

        # Save it to output
        self.log.info("Adding masked lidar data to {}".format(self.ds.filepath()))

        self.ds.variables['depth'][index,:] = new_ds.variables['Band1'][:]
        self.ds.sync()

        self.ds.close()
        new_ds.close()
        self.topo_ds.close()

    def get_time_index(self):
        """
        Calculates the time based index in hours for current image to go into the
        existing netcdf for lidar depths
        """
        # Get the timestep in hours. Set all images to 2300
        self.log.debug("Calculating the time index...")

        times = self.ds.variables['time']

        tstep = pd.to_timedelta(1, unit='h')
        t = nc.date2num(self.date+pd.to_timedelta(23, unit='h'), times.units,
                                                                 times.calendar)

        # Figure out the time index
        if len(times) != 0:
            index = np.where(times[:] == t)[0]

            if index.size == 0:
                index = len(times)
            else:
                index = index[0]
        else:
            index = len(times)

        self.log.info("Input data is {} hours from the beginning of the water"
                      " year.".format(int(t)))

        self.ds.variables['time'][index] = t

        return index

    def check_topo_match(self):
        """
        Checks to see if the topo masks long name matches the basin name of the
        image
        """

        topo_mask = self.topo_ds.variables['mask'].long_name.lower()

        # Flexible naming convention in the topo to check for matches
        keywords = [w for w in topo_mask.split(" ") if w not in ['river','basin']]

        for key in keywords:
            if key in self.basin.lower():
                found = True
                break
            else:
                found = False

        self.handle_error("Topo's mask name matches the basin name.",
                         ("Topo's mask ({}) is not associated to the {}."
                                               "".format(topo_mask, self.basin)),
                          error= not found)


    def check_water_year_match(self):
        """
        Checks if the the current images date and the existing lidar depths
        are in the same water year.
        """
        time_units = self.ds.variables['time'].units

        # Calculate the WY from the time units
        nc_wy = pd.to_datetime(time_units.split("since")[-1]).year + 1

        error = int(nc_wy) != self.water_year

        dbgmsg = "Input image water year matches prexisting netcdf's"
        errmsg = ("Attempting to add an image apart of water year {} "
                 " to an existing lidar depths netcdf for water year {}"
                 "".format(self.water_year, nc_wy))

        self.handle_error(dbgmsg, errmsg, error=error)

    def check_basin_match(self):
        """
        Checks that the basin name provided matches whats in the existing netcdf
        """
        error =  not self.basin.lower() in self.ds.getncattr("Title").lower()

        dbgmsg = "Basin entered matches the basin in the preexisting file."
        errmsg = ("The preexisting lidar depths file has a title of {} which"
             " should contain {} to add this image."
             "".format( self.ds.getncattr("Title"), self.basin))

        self.handle_error(dbgmsg, errmsg, error=error)


    def check_overwrite(self):
        """
        Checks that the netcdf doesn't already contain this date for a flight
        """

        times = self.ds.variables['time']
        ncdates = nc.num2date(times[:], times.units, calendar=times.calendar)
        ncdates = np.array([pd.to_datetime(dt).date() for dt in ncdates])

        # Is the incoming date already in the file?
        error = self.date.date() in ncdates
        errmsg = ("This image's date is already in the preexisting netcdf.")
        dbgmsg = ("Incoming date appears to be unique to the dataset.")
        self.handle_error(dbgmsg, errmsg, error=error)


def main():

    p = argparse.ArgumentParser(description="Modifies existing images to a"
                                            " different scale and shifts the"
                                            " grid to match modeling domains"
                                            " for SMRF/AWSM")

    p.add_argument("-t", "--topo", dest="topo",
                    required=True,
                    help="Path to the topo.nc file used for modeling")

    p.add_argument("-i", "--images", dest="images",
                    required=True, nargs='+',
                    help="Path to lidar images for processing")

    p.add_argument("-b", "--basin", dest="basin",
                    required=True, choices=['brb', 'kaweah', 'kings', 'lakes',
                                            'merced', 'sanjoaquin','tuolumne'],
                    help="Name of the basin to use for metadata")

    p.add_argument("-o", "--output", dest="output",
                    required=False,
                    help="Path to output folder")

    p.add_argument("-d", "--debug", dest="debug",
                    required=False, action='store_true',
                    help="Outputs more information and does not delete any"
                         " working files generated during runs")

    p.add_argument("-dt", "--date", dest="date",
                    required=False, default=None,
                    help="Enables user to directly control the date.")

    p.add_argument("-e", "--allow_exceptions", dest="allow_exceptions",
                    required=False, action="store_true",
                    help="For Development purposes, allows it to be debugging"
                    " but also enables the errors to NOT catch, which is useful"
                    " for batch processing.")

    args = p.parse_args()

    # Global debug variable
    global DEBUG
    DEBUG = args.debug

    start = time.time()
    skips = 0

    # Make sure our output folder exists
    if args.output == None:
        output = './output'
        temp = os.path.join(output,'tmp')

        # Make the output folder
        if not os.path.isdir(output):
            os.mkdir(output)

        # Make the temp folder inside the output folder
        if not os.path.isdir(temp):
                os.mkdir(temp)

    if type(args.images) != list:
        args.images = [args.images]


    # Get logger and add color with a simple format
    log = logging.getLogger(__name__)
    coloredlogs.install(fmt='%(levelname)-5s %(message)s', level="INFO",
                                                           logger=log)
    # Print a nice header with version number
    msg = "\n\nGrid Resizing and Matching Script v{}".format(BASIN_SETUP_VERSION)
    header = "=" * (len(msg) + 1)
    log.info(msg + "\n" + header + "\n")

    # We need to sort the images by date so create a dictionary of the two here
    log.info("Calculating dates and sorting images for processing...")
    dates = [parse_fname_date(f) for f in args.images]
    image_dict = {k:v for (k,v) in zip(dates, args.images)}

    # Loop through all images provided
    log.info("Number of images being processed: {}".format(len(args.images)))

    for k in sorted(image_dict.keys()):
        f = image_dict[k]

        log.info("")
        log.info("Processing {}".format(os.path.basename(f)))

        if not DEBUG or args.allow_exceptions:
            try:
                g = GRM(image=f, topo=args.topo, basin=args.basin,
                                                          debug=args.debug,
                                                          output=output,
                                                          temp=temp,
                                                          log=log)
                g.grid_match()
                g.add_to_collection()

            except:
                log.warning("Skipping {} due to error".format(
                                                           os.path.basename(f)))
                skips +=1

        else:
            g = GRM(image=f, topo=args.topo, basin=args.basin,
                                                      debug=args.debug,
                                                      output=output,
                                                      temp=temp,
                                                      log=log)
            g.grid_match()
            g.add_to_collection()
    stop = time.time()

    # Throw a warning when all get skipped
    if skips == len(args.images):
        log.warning("No images were processed!")

    g.log.info("Grid Resizing and Matching Complete. {1}/{2} files processed."
               " Elapsed Time {0:0.1f}s"
            "".format(stop-start, len(args.images) - skips, len(args.images)))

    if not DEBUG:
       log.info('Cleaning up temporary files.')
       shutil.rmtree(g.temp)

if __name__ == '__main__':
    main()
