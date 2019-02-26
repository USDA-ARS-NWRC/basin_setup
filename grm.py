#!/usr/bin/env python3

import argparse
import numpy as np
import os
from subprocess import check_output
import sys
import time
import geopandas as gpd
import datetime
import shutil
import coloredlogs
import netCDF4
from spatialnc.topo import get_topo_stats
import logging
from inicheck.utilities import mk_lst, remove_chars


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
            setattr(self,k,v)

        # Setup external logging if need be
        if not hasattr(self,'log'):
            self.log = logging.getLogger(__name__)

        # Manage Logging
        level="INFO"
        if hasattr(self,'debug'):
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

    def grid_match(self):
        """
        Interpolates the newly scaled grid to the current grid
        """

        outfile = os.path.basename(self.image)
        print(outfile)
        self.log.info("Rescaling image raster from {} to {}"
                    "".format(self.image_info['pixel size'][0], self.ts['du']))


        outfile, ext = outfile.split(".")
        outfile = outfile + ".nc"
        self.log.debug("Writing grid adjusted image to :\n{}".format(outfile))
        cmd = ["gdalwarp",
               "-of NETCDF",
               "-tap",
               "-te {} {} {} {}".format(int(np.min(self.ts["x"])), int(np.min(self.ts["y"])),
                                  int(np.max(self.ts["x"])), int(np.max(self.ts["y"]))),
               "-tr {} {}".format(int(abs(self.ts['du'])), int(abs(self.ts['dv']))),
               self.image,
               outfile]

        self.log.debug("Executing: {}".format(" ".join(cmd)))
        s = check_output(" ".join(cmd), shell=True)


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
    p.add_argument("-o", "--output", dest="output",
                    required=False,
                    help="Path to output folder")

    p.add_argument("-d", "--debug", dest="debug",
                    required=False, action='store_true')

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

    g = GRM(image=args.image, topo=args.topo, debug=args.debug,
                                                   output=output,
                                                   temp=temp,
                                                   log=log)
    g.grid_match()

    stop = time.time()
    g.log.info("Grid Resizing and Matching Complete. Elapsed Time {0}s"
            "".format(int(stop-start)))

if __name__ == '__main__':
    main()
