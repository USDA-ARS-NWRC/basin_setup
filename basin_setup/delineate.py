#!/usr/bin/env python3

import argparse
import datetime
import os
import shutil
import sys
import time
from subprocess import check_output

import geopandas as gpd
import numpy as np
from colorama import Fore, Style, init

from basin_setup import __version__

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

    if outfile and not os.path.isdir(folder):
        out.error("Directory provided for output location does not exist!"
                  "\nMissing----->{}".format(filename))
        sys.exit()

    if not outfile and not os.path.isfile(filename):
        out.error("Input file does not exist!\nMissing----->{}"
                  "".format(filename))
        sys.exit()


def run_cmd(cmd, nthreads=None):
    """
    Executes the command and pipes the output to the console.
    Args:
        cmd: String command to be entered in the the command prompt
    """

    out.dbg('Running {}'.format(cmd))
    if nthreads is not None:
        cmd = 'mpiexec -n {0} '.format(nthreads) + cmd

    s = check_output(cmd, shell=True, universal_newlines=True)
    out.dbg(s)


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

    if outfile is None:
        outfile = 'filled.tif'

    check_path(demfile)
    check_path(outfile, outfile=True)

    CMD = "pitremove -z {0} -fel {1}".format(demfile, outfile)

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
    out.msg(
        "Performing stream estimation using threshold of {0}".format(
            threshold))
    check_path(areaD8)
    check_path(threshold_streams_out, outfile=True)

    CMD = "threshold -ssa {0} -src {1} -thresh {2}".format(
        areaD8,
        threshold_streams_out,
        threshold)

    run_cmd(CMD, nthreads=nthreads)


def outlets_2_streams(d8flowdir, threshold_streams, pour_points,
                      new_pour_points=None,
                      nthreads=None):
    """
    STEP #5  Move Outlets to Streams, so as to move the catchment outlet point
    on one of the DEM cells identified by TauDEM as belonging to the
    stream network

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

    CMD = 'aread8 -p {0} -o {1} -ad8 {2}'.format(d8flowdir,
                                                 basin_outlets_moved,
                                                 areaD8_out)

    run_cmd(CMD, nthreads=nthreads)


def delineate_streams(dem, d8flowdir, basin_drain_area, threshold_streams,
                      basin_outlets_moved, stream_orderfile=None,
                      treefile=None, coordfile=None, netfile=None,
                      wfile=None, nthreads=None):
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
    CMD = 'gdal_translate -of AAIGrid {0} {1}'.format(infile, outfile)
    run_cmd(CMD)


def produce_shapefiles(watershed_tif, corrected_points,
                       output_dir=None, streamflow=False):
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

    wfname = os.path.basename(watershed_tif).split('.')[0] + '.shp'

    # Polygonize creates a raster with all subbasins
    watershed_shp = os.path.join(output_dir, wfname)
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
                # Create a new dataframe and output it
                df = gpd.GeoDataFrame(columns=wdf.columns, crs=wdf.crs)
                df = df.append(wdf.loc[idx])
                out.msg("Creating the subbasin outline for {}...".format(nm))

                df.to_file(os.path.join(output_dir, '{}_subbasin.shp'
                                        ''.format(
                                            (nm.lower()).replace(' ', '_'))
                                        ))

    # Output the full basin outline
    out.msg("Creating the entire basin outline...")
    same = np.ones(len(wdf.index))
    wdf['all'] = same
    basin_outline = wdf.dissolve(by='all')
    basin_outline.to_file(os.path.join(output_dir, 'basin_outline.shp'))

    return watershed_shp


def create_readme(sysargs, output_dir):
    """
    Creates a readme with all the details for creating the files
    Args:
        sysargs: command used for generating files
    """
    dt = ((datetime.datetime.today()).isoformat()).split('T')[0]
    out_str = (
        "###################################################################\n"
        "# BASIN DELINEATION TOOL V{0}\n"
        "###################################################################\n"
        "\n The files in this folder were generated on {1}.\n"
        "This was accomplished using the following command:\n"
        "\n$ {2}\n"
        "\nTo get access to the source code please visit:\n"
        "https://github.com/USDA-ARS-NWRC/basin_setup")

    out_str = out_str.format(__version__, dt, ' '.join(sys.argv))
    with open(os.path.join(output_dir, 'README.txt'), 'w') as fp:
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
        at_start: If at the beginning we cleanup a lot more files versus
            than at the end of a run.

    """
    out.msg("Cleaning up files...")

    # Always cleanup the temp folder
    temp = os.path.join(output_dir, 'temp')
    if os.path.isdir(temp):
        shutil.rmtree(temp)

    if at_start:
        # Remove any potential streamflow folders
        streamflow = os.path.join(output_dir, 'streamflow')
        if os.path.isdir(streamflow):
            shutil.rmtree(streamflow)

        fnames = os.listdir(output_dir)

        for f in fnames:
            fn = os.path.join(output_dir, f)
            if ("_subbasin." in f or "thresh" in f or "basin_outline." in f
                or 'watersheds_' in f or 'out.' in f
                    or "corrected_points_" in f):
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
                    move_forward = True

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


def create_ars_streamflow_files(treefile, coordfile, threshold, wshp, netdir,
                                output='basin_catchments.csv'):
    """
    Takes in the Tree file and the Coordinates file to produce a csv of the
    downstream catchment, the elevation of a catchment, and contributing area
    """
    today = (datetime.datetime.today().date()).isoformat()

    header = ("#############################################################\n"
              " Basin Catchment File for USDA-ARS-NWRC Streamflow modeling. \n"
              " Delineatation Threshold: {}\n"
              " Date Created: {}\n"
              " Created using basin_setup v{}\n"
              "#############################################################\n"
              "\n".format(threshold, today,
                          __version__)
              )

    with open(output, 'w+') as fp:
        fp.write(header)
        fp.close()

    # tree_names = ['link', 'start number', 'end number', 'downstream',
    #               'upstream',
    #               'strahler',
    #               'monitor point',
    #               'network magnitude']
    # coord_names = ['dummy', 'x', 'y', 'distance', 'elevation', 'area']

    # dftree = pd.read_csv(treefile, delimiter='\t', names=tree_names)
    # dfcoord = pd.read_csv(coordfile, delimiter='\t', names=coord_names)
    dfwshp = gpd.read_file(wshp)

    # Get the network shpapefile which lives under a folder named after the
    # tif.
    name = os.path.split(netdir)[-1].split('.')[0] + '.shp'
    netshp = os.path.join(netdir, name)
    dfnet = gpd.read_file(netshp)

    dfnet = dfnet.set_index('WSNO')

    # Collect the area of each basin
    dfwshp['area'] = dfwshp.area
    # handle individual cells acting as subbasins
    dfwshp = dfwshp.groupby('DN').sum()

    # Collect down stream info.
    dfwshp['downstream'] = dfnet['DSLINKNO']

    dfwshp.to_csv(output, mode='a')


def output_streamflow(imgs, threshold, wshp, temp="temp",
                      output_dir='streamflow'):
    """
    Outputs files necessary for streamflow modeling. This will create a file
    structure under a folder defined by output_dir and the threshold.
    E.g. streamflow/thresh_10000000

    Args:
        imgs: Dictionary containing a files to be outputted.
        threshold: threshold used for creating subbasins
        wshp: Watershed shapefile
        output_dir: Location to output files
    """
    # Dictionary to grab filenames for ARS streamflow
    dat = {}
    out.msg("Creating streamflow files...")

    final_output = os.path.join(output_dir, "thresh_{}".format(threshold))

    if not os.path.isdir(output_dir):
        out.msg("Making streamflow directory")
        os.mkdir(output_dir)

    if not os.path.isdir(final_output):
        out.msg("Making streamflow threshold directory...")
        os.mkdir(final_output)

    # Convert the watersheds to ascii and move files to streamflow folder for
    # SLF streamflow
    for k in ['corrected_points', 'watersheds', 'coord', 'tree']:

        name = os.path.basename(imgs[k])

        outfile = os.path.join(final_output, k + "." + name.split('.')[-1])

        # Handle grabbing data for outputing ARS streamflow
        if k in ['tree', 'coord']:
            dat[k] = outfile

        if k == 'watersheds':
            outfile = os.path.join(final_output, k + '.asc')
            convert2ascii(imgs[k], outfile)

        else:
            shutil.copy(imgs[k], outfile)

    # Copy over threshold files
    for f in os.listdir(imgs['net']):
        to_f = os.path.join(final_output, os.path.basename(f))
        shutil.copy(os.path.join(imgs["net"], f), to_f)

    # Create the files for ARS Streamflow
    create_ars_streamflow_files(dat['tree'],
                                dat['coord'],
                                threshold,
                                wshp,
                                imgs['net'],
                                output=os.path.join(final_output,
                                                    'basin_catchments.csv'))


def ernestafy(demfile, pour_points, output=None, temp=None, threshold=100,
              rerun=False,
              nthreads=None,
              out_streams=False):
    """
    Run TauDEM using the script Ernesto Made.... therefore we will
    ernestafy this basin.

    Args:
        demfile: Original DEM tif.
        pour_points: Locations of the pour_points in a .bna file format
        output: Output folder location, default is ./delineation
        threshold: Threshold to use, can be a list or a single value
        rerun: boolean indicating whether to avoid re-doing steps 1-3
        out_streams: Boolean determining whether to output the files for
                     streamflow modeling
    """

    create_readme(sys.argv, output)

    # Output File keys without a threshold in the filename
    non_thresholdkeys = ['filled', 'flow_dir', 'slope', 'drain_area',
                         'basin_drain_area']

    # Output File keys WITH a threshold in the filename
    thresholdkeys = ['thresh_streams', 'thresh_basin_streams', 'order', 'tree',
                     'coord', 'net', 'watersheds', 'basin_outline',
                     'corrected_points']

    filekeys = non_thresholdkeys + thresholdkeys

    # Create file paths for the output file management
    imgs = {}
    for k in filekeys:
        base = os.path.join(output, k)

        # Add the threshold to the filename if need be
        if k in thresholdkeys:
            base = os.path.join(temp, k)
            base += '_thresh_{}'.format(threshold)

        # Watchout for shapefiles
        if 'points' in k:
            imgs[k] = base + '.shp'
        # Files we need for streamflow
        elif k in ['coord', 'tree']:
            imgs[k] = base + '.dat'
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

            # 2. D8 Flow Directions in order to compute the flow direction in
            #    each DEM cell
            calcD8Flow(imgs['filled'], d8dir_file=imgs['flow_dir'],
                       d8slope_file=imgs['slope'],
                       nthreads=nthreads)

            # 3. D8 Contributing Area so as to compute the drainage area in
            #    each DEM cell
            calcD8DrainageArea(imgs['flow_dir'], areaD8_out=imgs['drain_area'],
                               nthreads=nthreads)
        else:
            out.msg("Please use the '--rerun' flag to perform a rerun.\n")
            sys.exit()

    ##########################################################################
    # This section and below gets run every call. (STEPS 4-8)
    ##########################################################################

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
                             threshold_streams_out=imgs['thresh_basin_streams'],  # noqa
                             threshold=threshold,
                             nthreads=nthreads)

    # 8. Stream Reach And Watershed
    delineate_streams(demfile, imgs['flow_dir'], imgs['basin_drain_area'],
                      imgs['thresh_basin_streams'], imgs['corrected_points'],
                      stream_orderfile=imgs['order'], treefile=imgs['tree'],
                      coordfile=imgs['coord'], netfile=imgs['net'],
                      wfile=imgs['watersheds'], nthreads=nthreads)

    # Output the shapefiles of the watershed
    wshp = produce_shapefiles(imgs['watersheds'], imgs['corrected_points'],
                              output_dir=output)
    if out_streams:
        output_streamflow(imgs, threshold, wshp, temp=temp,
                          output_dir=os.path.join(output, 'streamflow'))


def main():

    p = argparse.ArgumentParser(description='Delineates a new basin for'
                                ' SMRF/AWSM/Streamflow')

    p.add_argument("-d", "--dem", dest="dem",
                   required=True,
                   help="Path to dem")
    p.add_argument("-p", "--pour", dest="pour_points",
                   required=True,
                   help="Path to a .bna of pour points")
    p.add_argument("-o", "--output", dest="output",
                   required=False,
                   help="Path to output folder")
    p.add_argument("-t", "--threshold", dest="threshold",
                   nargs="+", default=[100],
                   help="List of thresholds to use for defining streams from"
                         " the flow accumulation, default=100")
    p.add_argument("-n", "--nthreads", dest="nthreads",
                   required=False,
                   help="Cores to use when processing the data")
    p.add_argument("-re", "--rerun", dest="rerun",
                   required=False, action='store_true',
                   help="Boolean Flag that determines whether to run the "
                   "script from the beginning or assume that the flow "
                   "accumulation has been completed once")
    p.add_argument("-db", "--debug", dest="debug",
                   required=False, action='store_true')
    p.add_argument('-strm', '--streamflow', dest='streamflow', required=False,
                   action='store_true', help='Use to'
                   ' output the necessary files for'
                   ' streamflow modeling')
    args = p.parse_args()
    # Global debug variable
    global DEBUG
    DEBUG = args.debug

    start = time.time()

    # Print a nice header
    msg = "Basin Delineation Tool v{0}".format(__version__)
    m = "=" * (2 * len(msg) + 1)
    out.msg(m, 'header')
    out.msg(msg, 'header')
    out.msg(m, 'header')

    rerun = args.rerun

    # Make sure our output folder exists
    if args.output is None:
        output = './delineation'
    else:
        output = args.output

    temp = os.path.join(output, 'temp')
    if not os.path.isdir(output):
        os.mkdir(output)
    else:
        cleanup(output, at_start=True)

    if not os.path.isdir(temp):
        os.mkdir(temp)

    # Cycle through all the thresholds provided
    for i, tr in enumerate(args.threshold):
        if i > 0:
            rerun = True

        ernestafy(args.dem, args.pour_points, output=output, temp=temp,
                  threshold=tr,
                  rerun=rerun,
                  nthreads=args.nthreads,
                  out_streams=args.streamflow)
    if not args.debug:
        cleanup(output, at_start=False)

    stop = time.time()
    out.msg("Basin Delineation Complete. Elapsed Time {0}s".format(
        int(stop - start)))


if __name__ == '__main__':
    main()
