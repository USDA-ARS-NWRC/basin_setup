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
BASIN_SETUP_VERSION = '0.7.9'

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
                                                  "".format(self.ts['du'],
                                                            self.ts['units']))
        # Get aso super depth info
        self.image_info = parse_gdalinfo(self.image)

        # output netcdf
        self.outfile = os.path.join(self.output, "lidar_depths.nc")

        # Titling
        renames = {"brb":"boise river basin",
                   "lakes":"mammoth lakes basin"}

        if self.basin in renames.keys():
            self.basin = renames[self.basin]
        else:
            self.basin = "{} river basin".format(self.basin)
        self.basin = self.basin.title()

        self.log.info("Working on the {}".format(self.basin))

    def grid_match(self):
        """
        Interpolates the newly scaled grid to the current grid
        """

        outfile = os.path.basename(self.image)

        self.log.info("Rescaling image raster from {} to {}"
                    "".format(self.image_info['pixel size'][0], self.ts['du']))


        outfile, ext = outfile.split(".")
        outfile = outfile + ".nc"
        self.working_file = outfile

        self.log.debug("Writing grid adjusted image to :\n{}".format(outfile))
        cmd = ["gdalwarp",
               "-of NETCDF",
               "-tap",
               "-overwrite",
               "-te {} {} {} {}".format(int(np.min(self.ts["x"])),
                                        int(np.min(self.ts["y"])),
                                        int(np.max(self.ts["x"])),
                                        int(np.max(self.ts["y"]))),
               "-tr {} {}".format(int(abs(self.ts['du'])),
                                  int(abs(self.ts['dv']))),
               self.image,
               outfile]

        self.log.debug("Executing: {}".format(" ".join(cmd)))
        s = check_output(" ".join(cmd), shell=True)

    def parse_fname_date(self):
        """
        Attempts to parse the date from the filename
        """
        bname = os.path.basename(self.image)

        # Only grab the numbers in the basename
        str_dt = "".join([c for c in bname if c.isnumeric()])
        dt = pd.to_datetime(str_dt)

        return dt

    def add_to_collection(self):
        """
        Adds a new netcdf to an existing one that includes all the metadata.
        If the existing file doesn't actually exist, it will create one.
        """
        if not hasattr(self, "date"):
            self.date = self.parse_fname_date()

        else:
            self.date = pd.to_datetime(self.date)

        self.log.info("Lidar Flight for {}".format(
                                           self.date.isoformat().split('T')[0]))

        if not hasattr(self, "epsg"):
            pass

        # Grab a human readable timefor today
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create a netcdf
        if not os.path.isfile(self.outfile):
            self.log.info("Output NetCDF does not exist, creating a new one!")

            # Exclude all variables except dimensions
            ds = nc.Dataset(self.topo, mode='r')
            ex_var = [v for v in ds.variables if v.lower() not in ['x','y']]
            ds.close()

            # Copy a topo like netcdf image to add depths to
            ds = copy_nc(self.topo, self.outfile, exclude=ex_var)
            ds.createDimension("time", None)

            # Determine 10-1 date
            yr = self.date.year

            if self.date.month <= 10:
                yr -= 1

            start_date = datetime.date(yr, 10, 1)
            self.log.debug("Using {} as start of water year for stamping netcdf"
            "".format(start_date.isoformat()))

            # Assign time and count days since 10-1
            times = ds.createVariable('time', 'int', ('time'))
            setattr(ds.variables['time'], 'units', 'days since %s' % start_date)
            setattr(ds.variables['time'], 'calendar', 'standard')

            # Add append a newm image
            ds.createVariable("depth", "f", ("time", "y", "x"),
                                            chunksizes=(6, 10, 10))
            # Adjust global attributes
            ds.setncatts({"last_modified":now,
                        "dateCreated":now,
                        "Title":"ASO 50m Lidar Flights over the {}."
                                "".format(self.basin),
                        "history":"Created using Basin Setup v{}"
                                  "".format(BASIN_SETUP_VERSION),
                        })

            # Attribute gets copied over from the topo
            ds.delncattr("generation_command")

        else:
            self.log.info("Output NetCDF exists, appending data to it!")
            ds = nc.Dataset(self.outfile, mode='w')
            times = ds.variables['time']
            ds.setncatts({"last_modified":now})

        tstep = pd.to_timedelta(1, unit='D')
        t = nc.date2num(self.date, times.units, times.calendar)

        # Figure out the time index
        if len(times) != 0:
            index = np.where(times[:] == t)[0]

            if index.size == 0:
                index = len(times)
            else:
                index = index[0]
        else:
            index = len(times)

        ds.variables['time'][index] = t

        # ds.close()
        # ds = mask_nc(self.outfile, exclude)



def main():

    p = argparse.ArgumentParser(description="Modifies existing images to a"
                                            " different scale and shifts the"
                                            " grid to match modeling domains"
                                            " for SMRF/AWSM")

    p.add_argument("-t", "--topo", dest="topo",
                    required=True,
                    help="Path to the topo.nc file used for modeling")

    p.add_argument("-i", "--image", dest="image",
                    required=True,
                    help="Path to an image for processing")

    p.add_argument("-b", "--basin", dest="basin",
                    required=True, choices=['brb', 'kaweah', 'kings', 'lakes',
                                            'merced', 'sanjoaquin','tuolumne'],
                    help="Name of the basin to use for metadata")

    p.add_argument("-o", "--output", dest="output",
                    required=False,
                    help="Path to output folder")

    p.add_argument("-d", "--debug", dest="debug",
                    required=False, action='store_true')

    p.add_argument("-dt", "--date", dest="date",
                    required=False, default=None,
                    help="Enables user to directly control the date.")

    args = p.parse_args()

    # Global debug variable
    global DEBUG
    DEBUG = args.debug

    start = time.time()

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

    # Get logger and add color with a simple format
    log = logging.getLogger(__name__)
    coloredlogs.install(fmt='%(levelname)-5s %(message)s', level="INFO",
                                                           logger=log)
    msg = "\n\nGrid Resizing and Matching Script v{}".format(BASIN_SETUP_VERSION)
    header = "=" * (len(msg) + 1)
    log.info(msg + "\n" + header + "\n")

    g = GRM(image=args.image, topo=args.topo, basin=args.basin,
                                              debug=args.debug,
                                              output=output,
                                              temp=temp,
                                              log=log)
    g.grid_match()
    g.add_to_collection()

    stop = time.time()
    g.log.info("Grid Resizing and Matching Complete. Elapsed Time {0:0.1f}s"
            "".format(stop-start))

if __name__ == '__main__':
    main()
