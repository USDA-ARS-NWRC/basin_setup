#!/usr/bin/env python3

import argparse
import numpy as np
import os
from subprocess import Popen, PIPE, check_output,STDOUT
import sys
from colorama import init, Fore, Back, Style
import time
import geopandas as gpd
import datetime
import shutil

DEBUG=False
BASIN_SETUP_VERSION = '0.7.5'


class Messages():
    def __init__(self):
        self.context = {'warning':Fore.YELLOW,
                        'error':Fore.RED,
                        'ok': Fore.GREEN,
                        'normal': Style.NORMAL+Fore.WHITE,
                        'header': Style.BRIGHT}

    def build_msg(self,str_msg,context_str=None):
        """
        Constructs the desired strings for color and Style

        Args;
            str_msg: String the user wants to output
            context_str: type of print style and color, key associated with
                         self.context
        Returns:
            final_msg: Str containing the desired colors and styles
        """

        if context_str == None:
            context_str = 'normal'

        if context_str in self.context.keys():
            if type(str_msg) == list:
                str_msg = ', '.join([str(s) for s in str_msg])

            final_msg = self.context[context_str]+ str_msg + Style.RESET_ALL
        else:
            raise ValueError("Not a valid context")
        return final_msg

    def _structure_msg(self, a_msg):
        if type(a_msg) == list:
            a_msg = ', '.join([str(s) for s in a_msg])

        if type(a_msg)!=str:
            a = str(a_msg)

        return a_msg

    def msg(self,str_msg,context_str=None):
        final_msg = self.build_msg(str_msg,context_str)
        print('\n' + final_msg)

    def dbg(self,str_msg,context_str=None):
        """
        Messages designed for debugging set by a global variable DEBUG
        """
        if DEBUG:
            final_msg = self.build_msg('[DEBUG]: ','header')
            final_msg += self._structure_msg(str_msg)
            final_msg = self.build_msg(final_msg,context_str)
            print('\n' + final_msg)

    def warn(self,str_msg):
        final_msg = self.build_msg('[WARNING]: ','header')
        final_msg = self.build_msg(final_msg+str_msg, 'warning')
        print('\n' + final_msg)

    def error(self,str_msg):
        final_msg = self.build_msg('[ERROR]: ','header')
        final_msg = self.build_msg(final_msg+str_msg,'error')
        print('\n' + final_msg)

    def respond(self,str_msg):
        """
        Messages acting like a confirmation to the user and in response to the
        previous message
        """
        final_msg = self.build_msg(str_msg, 'ok')
        print('\t' + final_msg)

out = Messages()


def check_path(filename, outfile=False):
    """
    Checks whether an file has been provided exists.
    If outfile is true then we assume we are making a file and there fore we
    should only check if the directory exists.

    Args:
        filename: path to a file
        outfile: Boolean indicating whether to check for a file (outfile=False)
                 or a directory (outfile==True)
    """
    folder = os.path.dirname(filename)

    if outfile==True and not os.path.isdir(folder):
        out.error("Directory provided for output location does not exist!"
                  "\nMissing----->{}".format(filename))
        sys.exit()

    if not outfile and not os.path.isfile(filename):
        out.error("Input file does not exist!\nMissing----->{}"
        "".format(filename))
        sys.exit()


def rename_file(original,add_tag):
    """
    Takes a filename and renames the file based on the add tag.
    E.g.
    original file = test.tif
    add_tag = new
    results in test_new.tif

    Args:
        original: original filename
        add_tag: appends to the original filename to make the new one unique
    Returns:
        rename: new filename containing the unqiqu filename
    """
    path = original.split('.')
    if len(path) > 2:
        out.error("Avoid using paths with extra '.' in  them.\n"
                  "Attempted to rename: {0}".format(original))
        sys.exit()

    p = path[0] + "_{}".format(add_tag) + path[-1]


def run_cmd(cmd, nthreads=None):
    """
    Executes the command and pipes the output to the console.
    Args:
        cmd: String command to be entered in the the command prompt
    """

    out.dbg('Running {}'.format(cmd))
    if nthreads != None:
        cmd = 'mpiexec -n {0} '.format(nthreads) + cmd

    s = check_output(cmd, shell=True, universal_newlines=True)
    out.dbg(s)


def get_docker_bash(cmd,nthreads=None):
    """
    Returns the string command for running in a docker.

    Args:
        cmd: string command that you would run in side of a terminal without mpi
        nthreads: Number of cores to use for mpiexec
    """
    # Added in threaded business
    if nthreads != None:
        cmd = 'mpiexec -n {0} --allow-run-as-root '.format(nthreads) + cmd

    # Docker has to entrypoint on the command and th args passed to the image
    args = cmd.split(' ')

    # make entrypoint take in the tau commands call
    action = ('docker run --rm -ti -w /home -v $(pwd):/home --entrypoint {0}'
              ' quay.io/wikiwatershed/taudem {1}').format(args[0],
                                                          " ".join(args[1:]))

    return action


def pitremove(demfile, outfile=None, nthreads=None):
    """
    STEP #1
    Builds the command to pit fill the DEM and executes it.

    Args:
        demfile: Path to tif of the DEM.
        outfile: Path to write the pit filled DEM.
        nthreads: Number of cores to use for mpiexec

    """
    out.msg("Removing Pits from DEM...")

    if outfile == None:
        outfile='filled.tif'

    check_path(demfile)
    check_path(outfile, outfile=True)

    CMD =  "pitremove -z {0} -fel {1}".format(demfile, outfile)
    ## action = get_docker_bash(CMD, nthreads=nthreads)
    run_cmd(CMD, nthreads=nthreads)


def calcD8Flow(filled_dem, d8dir_file=None, d8slope_file=None, nthreads=None):
    """
    STEP #2
    Builds the command to calculate the D8 flow for the flow direction and
    executes it.

    Args:
        filled_dem: Path to tif of the pit filled DEM.
        d8dir_file: Path to write the D8 flow direction.
        d8slope_file: Path to write the D8 flow slope.
        nthreads: Number of cores to use for mpiexec
    """

    out.msg("Calculating D8 flow direction...")

    # Check paths
    check_path(filled_dem)
    check_path(d8dir_file, outfile=True)
    check_path(d8slope_file, outfile=True)

    CMD = "d8flowdir -fel {0} -p {1} -sd8 {2}".format(filled_dem,
                                                         d8dir_file,
                                                         d8slope_file)
    # action = get_docker_bash(CMD, nthreads=nthreads)
    run_cmd(CMD, nthreads=nthreads)


def calcD8DrainageArea(d8flowdir, areaD8_out=None, nthreads=None):
    """
    STEP #3
    Calculates D8 Contributing area to each cell in the DEM.

    Args:
        d8flowdir: Path to the D8 Flow direction image
        areaD8_out: Path to output the Drainage area image
        nthreads: Number of cores to use for mpiexec
    """
    check_path(d8flowdir)
    check_path(areaD8_out, outfile=True)
    CMD = "aread8 -p {0} -ad8 {1}".format(d8flowdir, areaD8_out)
    # action = get_docker_bash(CMD, nthreads=nthreads)
    run_cmd(CMD, nthreads=nthreads)

def defineStreamsByThreshold(areaD8, threshold_streams_out=None, threshold=100,
                                                                 nthreads=None):
    """
    STEP #4
    Stream definition by threshold in order to extract a first version of the
    stream network

    Args:
        areaD8: Path to the D8 Drainage area image
        threshold_streams_out: Path to output the thresholded image
        threshold: threshold value to recategorize the data
        nthreads: Number of cores to use for mpiexec
    """
    out.msg("Performing stream estimation using threshold of {0}".format(threshold))
    check_path(areaD8)
    check_path(threshold_streams_out, outfile=True)

    CMD = "threshold -ssa {0} -src {1} -thresh {2}".format(areaD8,
                                                         threshold_streams_out,
                                                         threshold)
    # action = get_docker_bash(CMD, nthreads=nthreads)
    run_cmd(CMD, nthreads=nthreads)


def outlets_2_streams(d8flowdir, threshold_streams, pour_points,
                                                   new_pour_points=None,
                                                   nthreads=None):
    """
    STEP #5  Move Outlets to Streams, so as to move the catchment outlet point
    on one of the DEM cells identified by TauDEM as belonging to the stream network

    Args:
        d8flowdir: Path to the D8 Flow direction image
        threshold_streams: Path to output the thresholded stream image
        pour_points: Path to pour point locations in a list
        new_pour_points: Path to output the new list of points
        nthreads: Number of cores to use for mpiexec
    """

    check_path(d8flowdir)
    check_path(threshold_streams)
    check_path(pour_points)
    check_path(new_pour_points, outfile=True)
    CMD = 'moveoutletstostrm -p {0} -src {1} -o {2} -om {3}'.format(
                                                            d8flowdir,
                                                            threshold_streams,
                                                            pour_points,
                                                            new_pour_points)
    # action = get_docker_bash(CMD, nthreads=nthreads)
    run_cmd(CMD, nthreads=nthreads)


def calcD8DrainageAreaBasin(d8flowdir, basin_outlets_moved, areaD8_out=None,
                                                            nthreads=None):
    """
    STEP #6
    D8 Contributing Area again, but with the catchment outlet point as
    additional input data

    Args:
        d8flowdir: Path to the D8 Flow direction image
        basin_outlets_moved: all pour points that have been moved to the stream
        areaD8_out: Path to output the Drainage area image that utilize all the
                    points
        nthreads: Number of cores to use for mpiexec

    """
    out.msg("Calculating drainage area using pour points...")
    check_path(d8flowdir)
    check_path(basin_outlets_moved)
    check_path(areaD8_out, outfile=True)

    CMD = 'aread8 -p {0} -o {1} -ad8 {2}'.format(d8flowdir,basin_outlets_moved,
                                                               areaD8_out)
    # action = get_docker_bash(CMD, nthreads=nthreads)
    run_cmd(CMD, nthreads=nthreads)


def delineate_streams(dem, d8flowdir, basin_drain_area, threshold_streams,
                      basin_outlets_moved, stream_orderfile=None, treefile=None,
                      coordfile=None, netfile=None, wfile=None, nthreads=None):
    """
    STEP #8 Stream Reach And Watershed
    Args:
        dem: path to a filled dem image
        d8flowdir: path to the flow direction image
        basin_drain_area: path to the flow accumulation image for the basin
        threshold_streams: streams defintion image defined by a threshold
        basin_outlets_moved: Path to a .bna of the pour points corrected to be
                             on the streams.
        stream_orderfile: Name of the file to output the stream segment order
        treefile: Name of the file to output the subbasin flow order.
        coordfile: Not sure what this file is
        netfile: Name of the images to output the stream definitions.
        wfile: Name of the image to output subbasin definitions.
        nthreads: Number of cores to use for mpiexec
    """

    out.msg("Creating watersheds and stream files...")

    # Check path validity
    inputs = [dem, d8flowdir, basin_drain_area, threshold_streams,
              basin_outlets_moved]

    outputs = [stream_orderfile, treefile, coordfile, netfile, wfile]
    for f in inputs:
        check_path(f)

    for f in outputs:
        check_path(f, outfile=True)

    CMD = ('streamnet -fel {0} -p {1} -ad8 {2} -src {3} -ord {4} -tree {5}'
                     ' -coord {6} -net {7} -o {8} -w {9}').format(
                                                            dem,
                                                            d8flowdir,
                                                            basin_drain_area,
                                                            threshold_streams,
                                                            stream_orderfile,
                                                            treefile,
                                                            coordfile,
                                                            netfile,
                                                            basin_outlets_moved,
                                                            wfile)
    run_cmd(CMD, nthreads=nthreads)


def convert2ascii(infile, outfile=None):
    """
    Convert to ascii
    """
    check_path(infile)
    check_path(outfile, outfile=True)

    # convert wfile files to ascii
    CMD = 'gdal_translate -of AAIGrid {0} {1}'.format(infile,outfile)
    run_cmd(CMD, nthreads=nthreads)


def produce_shapefiles(watershed_tif, corrected_points, output_dir=None):
    """
    Outputs the polygons of the individual subbasins to a shapfile.

    Args:
        watershed_tif: Path to a geotiff of the watersheds
        corrected_points: Path to the corrected points used for delineation
        output_dir: Output location used for producing shapefiles
    """
    # Check files
    check_path(watershed_tif)
    check_path(corrected_points)

    # Polygonize creates a raster with all subbasins
    watershed_shp = os.path.join(output_dir,'watersheds.shp')
    CMD = 'gdal_polygonize.py -f "ESRI SHAPEFILE" {} {}'.format(watershed_tif,
                                                            watershed_shp)
    run_cmd(CMD)

    # Read in and identify the names of the pour points with the subbasins
    ptdf = gpd.read_file(corrected_points)

    wdf = gpd.read_file(watershed_shp)

    # Identify the name and output the individual basins
    for nm, pt in zip(ptdf['Primary ID'].values, ptdf['geometry'].values):
        for pol, idx in zip(wdf['geometry'].values, wdf.index):
            if pt.within(pol):
                #Create a new dataframe and output it
                df = gpd.GeoDataFrame(columns=wdf.columns, crs=wdf.crs)
                df = df.append(wdf.loc[idx])
                out.msg("Creating the subbasin outline for {}...".format(nm))

                df.to_file(os.path.join(output_dir,'{}_subbasin.shp'
                           ''.format((nm.lower()).replace(' ','_'))))

    # Output the full basin outline
    out.msg("Creating the entire basin outline...")
    same = np.ones(len(wdf.index))
    wdf['all'] = same
    basin_outline = wdf.dissolve(by='all')
    basin_outline.to_file(os.path.join(output_dir,'basin_outline.shp'))

def create_readme(sysargs, output_dir):
    """
    Creates a readme with all the details for creating the files
    Args:
        sysargs: command used for generating files
    """
    dt = ((datetime.datetime.today()).isoformat()).split('T')[0]
    out_str = (
    "########################################################################\n"
    "# BASIN DELINEATION TOOL V{0}\n"
    "########################################################################\n"
    "\n The files in this folder were generated on {1}.\n"
    "This was accomplished using the following command:\n"
    "\n$ {2}\n"
    "\nTo get access to the source code please visit:\n"
    "https://github.com/USDA-ARS-NWRC/basin_setup")

    out_str = out_str.format(BASIN_SETUP_VERSION, dt, ' '.join(sys.argv))
    with open(os.path.join(output_dir,'README.txt'),'w') as fp:
        fp.write(out_str)
        fp.close()


def cleanup(output_dir, at_start=False):
    """
    Removes the temp folder and removes the following files:
        * output/watersheds.shp
        * output/*_subbasin.shp
        * output/basin_outline.shp
        * output/corrected_points.shp

    Args:
        output_dir: folder to lookin for cleanup
        at_start: If at the beginning we cleanup a lot more files versus than at
                  the end of a run.

    """
    out.msg("Cleaning up files...")

    # Always cleanup the temp folder
    temp = os.path.join(output_dir,'temp')
    if os.path.isdir(temp):
        shutil.rmtree(temp)

    if at_start:
        fnames = os.listdir(output_dir)

        for f in fnames:
            fn = os.path.join(output_dir,f)
            if ("_subbasin." in f or "thresh" in f or "basin_outline." in f
                or 'watersheds.' in f or 'out.' in f
                or "corrected_points." in f):
                out.dbg("Removing {}".format(f))
                os.remove(fn)

def confirm_norerun(non_thresholdkeys, imgs):
    """
    Checks if the non-thresholded files exist, if so confirm the user wants
    to overwrite them.

    Args:
        non-thresholdedkeys: keys to check in the imgs dictionary of paths
        imgs: Dictionary of paths to images
    Returns
        bool: Indicating whether we continue or not
    """
    out.dbg("Checking if important delineation images pre-exist...")

    # Quickly check if the user wants to over write a possible rerun
    move_forward = False
    any_file_exists = False

    for f in non_thresholdkeys:

        if os.path.isfile(imgs[f]):
            out.dbg("{} image exists!".format(f))
            any_file_exists = True
            out.warn("You are about to overwrite the delineation files that"
                     " take the longest to make. \n\nAre you sure you want to"
                     " do this? (y/n)\n")
            answer = input()

            acceptable_answer = False
            while not acceptable_answer:

                if answer.lower() == 'y':
                    acceptable_answer = True
                    move_forward=True

                elif answer.lower() == 'n':
                    acceptable_answer = True

                else:
                    acceptable_answer = False
            break

    # If there weren't any files then move ahead
    if not any_file_exists:
        move_forward = True
        out.dbg("No pre-existing files, moving forward...")
    return move_forward


def ernestafy(demfile, pour_points, output=None, temp=None, threshold=100,
                                                                rerun=False,
                                                                nthreads=None):
    """
    Run TauDEM using the script Ernesto Made.... therefore we will
    ernestafy this basin.

    Args:
        demfile: Original DEM tif.
        pour_points: Locations of the pour_points in a .bna file format
        output: Output folder location, default is ./delineation
        threshold: Threshold to use, can be a list or a single value
        rerun: boolean indicating whether to avoid re-doing steps 1-3

    """

    create_readme(sys.argv, output)

    # Output File keys without a threshold in the filename
    non_thresholdkeys = ['filled','flow_dir','slope','drain_area',
                      'basin_drain_area', 'corrected_points']

    # Output File keys WITH a threshold in the filename
    thresholdkeys = ['thresh_streams', 'thresh_basin_streams', 'order', 'tree',
                     'coord', 'net', 'watersheds','basin_outline']

    filekeys = non_thresholdkeys + thresholdkeys

    # Create file paths for the output file management
    imgs = {}
    for k in filekeys:
        base = os.path.join(output,k)

        # Add the threshold to the filename if need be
        if k in thresholdkeys:
            base = os.path.join(temp,k)
            base += '_thresh_{}'.format(threshold)

        # Watchout for shapefiles
        if 'points' in k:
            imgs[k] = base + '.shp'
        else:
            imgs[k] = base + '.tif'

    # This file if it already exists causes problems
    if os.path.isfile(imgs['net']):
        out.msg("Removing pre-existing stream network file...")
        os.remove(imgs['net'])

    # If we rerun we don't want to run steps 1-3 again
    if rerun:
        out.warn("Performing a rerun, assuming files for flow direction and"
                " accumulation exist...")
    else:
        move_forward = confirm_norerun(non_thresholdkeys, imgs)
        if move_forward:
            # 1. Pit Remove in order to fill the pits in the DEM
            pitremove(demfile, outfile=imgs['filled'], nthreads=nthreads)

            # 2. D8 Flow Directions in order to compute the flow direction in each
            #    DEM cell
            calcD8Flow(imgs['filled'], d8dir_file=imgs['flow_dir'],
                                       d8slope_file=imgs['slope'], nthreads=nthreads)

            # 3. D8 Contributing Area so as to compute the drainage area in each
            #    DEM cell
            calcD8DrainageArea(imgs['flow_dir'], areaD8_out=imgs['drain_area'],
                                                 nthreads=nthreads)
        else:
            out.msg("Please use the '--rerun' flag to perform a rerun.\n")
            sys.exit()

    ############################################################################
    # This section and below gets run every call. (STEPS 4-8)
    ############################################################################

    # 4. Stream Definition by Threshold, in order to extract a first version of
    #    the stream network
    defineStreamsByThreshold(imgs['drain_area'],
                             threshold_streams_out=imgs['thresh_streams'],
                             threshold=threshold, nthreads=nthreads)

    # 5. Move Outlets to Streams, so as to move the catchment outlet point on
    #    one of the DEM cells identified by TauDEM as belonging to the stream
    #    network
    outlets_2_streams(imgs['flow_dir'], imgs['thresh_streams'], pour_points,
                                       new_pour_points=imgs['corrected_points'],
                                       nthreads=nthreads)

    # 6. D8 Contributing Area again, but with the catchment outlet point as
    #    additional input data
    calcD8DrainageAreaBasin(imgs['flow_dir'], imgs['corrected_points'],
                                         areaD8_out=imgs['basin_drain_area'],
                                         nthreads=nthreads)

    # 7. Stream Definition by Threshold again, but with the catchment outlet
    #    point as additional input data
    defineStreamsByThreshold(imgs['basin_drain_area'],
                             threshold_streams_out=imgs['thresh_basin_streams'],
                             threshold=threshold,
                             nthreads=nthreads)

    # 8. Stream Reach And Watershed
    delineate_streams(demfile, imgs['flow_dir'], imgs['basin_drain_area'],
                       imgs['thresh_basin_streams'], imgs['corrected_points'],
                       stream_orderfile=imgs['order'], treefile=imgs['tree'],
                       coordfile=imgs['coord'], netfile=imgs['net'],
                       wfile=imgs['watersheds'], nthreads=nthreads)

    # Output the shapefiles of the watershed
    produce_shapefiles(imgs['watersheds'], imgs['corrected_points'],
                                         output_dir=output)



def main():

    p = argparse.ArgumentParser(description='Delineates a new basin for'
                                ' SMRF/AWSM/Streamflow')

    p.add_argument("-d","--dem", dest="dem",
                    required=True,
                    help="Path to dem")
    p.add_argument("-p","--pour", dest="pour_points",
                    required=True,
                    help="Path to a .bna of pour points")
    p.add_argument("-o","--output", dest="output",
                    required=False,
                    help="Path to output folder")
    p.add_argument("-t","--threshold", dest="threshold",
                    nargs="+", default=[100],
                    help="List of thresholds to use for defining streams from"
                         " the flow accumulation, default=100")
    p.add_argument("-n","--nthreads", dest="nthreads",
                    required=False,
                    help="cores to use when processing the data")
    p.add_argument("-re","--rerun", dest="rerun",
                    required=False, action='store_true',
                    help="Boolean Flag that determines whether to run the "
                         "script from the beginning or assume that the flow "
                         "accumulation has been completed once")
    p.add_argument("-db","--debug", dest="debug",
                    required=False, action='store_true')
    args = p.parse_args()
    # Global debug variable
    global DEBUG
    DEBUG = args.debug

    start = time.time()

    # Print a nice header
    msg ="Basin Delineation Tool v{0}".format(BASIN_SETUP_VERSION)
    m = "="*(2*len(msg)+1)
    out.msg(m,'header')
    out.msg(msg,'header')
    out.msg(m,'header')

    rerun = args.rerun

    # Make sure our output folder exists
    if args.output == None:
        output = './delineation'
        temp = os.path.join(output, 'temp')
        if not os.path.isdir(output):
            os.mkdir(output)
        else:
            cleanup(output, at_start=True)

        if not os.path.isdir(temp):
                os.mkdir(temp)



    # Cycle through all the thresholds provided
    for i,tr in enumerate(args.threshold):
        if i > 0:
            rerun = True

        ernestafy(args.dem,args.pour_points, output=output, temp=temp,
                                                       threshold=tr,
                                                       rerun=rerun,
                                                       nthreads=args.nthreads)
    if not args.debug:
        cleanup(output, at_start=False)

    stop = time.time()
    out.msg("Basin Delineation Complete. Elapsed Time {0}s".format(int(stop-start)))

if __name__ == '__main__':
    main()
