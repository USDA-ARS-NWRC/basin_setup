#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import os
from subprocess import Popen, PIPE, check_output,STDOUT
import sys
from colorama import init, Fore, Back, Style

DEBUG=True


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
        out.error("Directory provided for output location does not exist!\nMissing----->{}".format(filename))
        sys.exit()

    if not outfile and not os.path.isfile(filename):
        out.error("Input file does not exist!\nMissing----->{}".format(filename))
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

def run_cmd(cmd):
    """
    Executes the command and pipes the output to the console.
    Args:
        cmd: String command to be entered in the the command prompt
    """

    out.dbg('Running {}'.format(cmd))

    s = check_output(cmd, shell=True, universal_newlines=True)
    out.dbg(s)
    # while True:
    #     line = s.stdout.readline()
    #     print(line.decode('utf-8'))
    #     if not line:
    #         break
    #s.wait()


def get_docker_bash(cmd,nthreads=None):
    """
    Returns the string command for running in a docker.
    """
    # Docker has to entrypoint on the command and th args passed to the image
    args = cmd.split(' ')
    # make entrypoint take in the tau commands call
    action = ('docker run --rm -ti -w /home -v $(pwd):/home --entrypoint {0}'
              ' quay.io/wikiwatershed/taudem {1}').format(args[0]," ".join(args[1:]))

    # # Added in threaded business
    # if nthreads != None:
    #     action+='mpiexec -n {0} '.format(nthreads)

    return action


def pitremove(demfile, outfile=None):
    """
    STEP #1
    Builds the command to pit fill the DEM and executes it.

    Args:
        demfile: Path to tif of the DEM.
        outfile: Path to write the pit filled DEM.
    """
    out.msg("Removing Pits from DEM...")

    if outfile == None:
        outfile='filled.tif'

    check_path(demfile)
    check_path(outfile, outfile=True)

    CMD =  "pitremove -z {0} -fel {1}".format(demfile, outfile)
    action = get_docker_bash(CMD)
    run_cmd(action)


def calcD8Flow(filled_dem, d8dir_file=None, d8slope_file=None):
    """
    STEP #2
    Builds the command to calculate the D8 flow for the flow direction and
    executes it.

    Args:
        filled_dem: Path to tif of the pit filled DEM.
        d8dir_file: Path to write the D8 flow direction.
        d8slope_file: Path to write the D8 flow slope.
    """

    out.msg("Calculating D8 flow direction...")

    # Check paths
    check_path(filled_dem)
    check_path(d8dir_file, outfile=True)
    check_path(d8slope_file, outfile=True)

    CMD = "d8flowdir -fel {0} -p {1} -sd8 {2}".format(filled_dem,
                                                         d8dir_file,
                                                         d8slope_file)
    action = get_docker_bash(CMD)
    run_cmd(action)


def calcD8DrainageArea(d8flowdir, areaD8_out=None):
    """
    STEP #3
    Calculates D8 Contributing area to each cell in the DEM.

    Args:
        d8flowdir: Path to the D8 Flow direction image
        areaD8_out: Path to output the Drainage area image
    """
    check_path(d8flowdir)
    check_path(areaD8_out,outfile=True)
    CMD = "aread8 -p {0} -ad8 {1}".format(d8flowdir, areaD8_out)
    action = get_docker_bash(CMD)
    run_cmd(action)

def defineStreamsByThreshold(areaD8, threshold_streams_out=None, threshold=1000):
    """
    STEP #4
    Stream definition by threshold in order to extract a first version of the
    stream network

    Args:
        areaD8: Path to the D8 Drainage area image
        threshold_streams_out: Path to output the thresholded image
        threshold: threshold value to recategorize the data
    """
    check_path(areaD8)
    check_path(threshold_streams_out, outfile=True)

    CMD = "threshold -ssa {0} -src {1} -thresh {2}".format(areaD8,
                                                         threshold_streams_out,
                                                         threshold)
    action = get_docker_bash(CMD)
    run_cmd(action)


def outlets_2_streams(d8flowdir, threshold_streams, pour_points,
                                                   new_pour_points=None):
    """
    STEP #5  Move Outlets to Streams, so as to move the catchment outlet point on one of
    the DEM cells identified by TauDEM as belonging to the stream network

    Args:
        d8flowdir: Path to the D8 Flow direction image
        threshold_streams: Path to output the thresholded stream image
        pour_points: Path to pour point locations in a list
        new_pour_points: Path to output the new list of points
    """

    check_path(d8flowdir)
    check_path(threshold_streams)
    check_path(pour_points)
    check_path(new_pour_points,outfile=True)
    CMD = 'moveoutletstostrm -p {0} -src {1} -o {2} -om {3}'.format(
                                                            d8flowdir,
                                                            threshold_streams,
                                                            pour_points,
                                                            new_pour_points)
    action = get_docker_bash(CMD)
    run_cmd(action)


def calcD8DrainageAreaBasin(d8flowdir, basin_outlets_moved, areaD8_out=None):
    """
    STEP #6
    D8 Contributing Area again, but with the catchment outlet point as
    additional input data

    Args:
        d8flowdir: Path to the D8 Flow direction image
        basin_outlets_moved: all pour points that have been moved to the stream
        areaD8_out: Path to output the Drainage area image that utilize all the points

    """
    check_path(d8flowdir)
    check_path(basin_outlets_moved)
    check_path(areaD8_out, outfile=True)

    CMD = 'aread8 -p {0} -o {1} -ad8 {2}'.format(d8flowdir,basin_outlets_moved,
                                                               areaD8_out)
    action = get_docker_bash(CMD)
    run_cmd(action)


def delineate_streams(dem, d8flowdir, basin_drain_area, threshold_streams,
                      basin_outlets_moved, stream_orderfile=None, treefile=None,
                      coordfile=None, netfile=None, wfile=None):
    """
    STEP #8 Stream Reach And Watershed

    Original cmd
        streamnet -fel topo_50m_fel.tif
                      -p topo_50m_d8flowdir.tif
                      -ad8 topo_50m_aread8_allweirs.tif
                      -src topo_50m_thres100_tollgate.tif
                      -ord tollgate_stream_orderfile_100.tif
                      -tree tollgate_treefile_100.dat
                      -coord tollgate_coordfile_100.dat
                      -net tollgate_netfile_100.shp
                      -o tollgate_weirs_xyz_moved.shp
                      -w tollgate_wfile_100.tif
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
    action = get_docker_bash(CMD)
    run_cmd(action)

def ernestafy(demfile, pour_points, output=None, threshold=100, rerun=True):
    """
    Run TauDEM using the script Ernesto Made.... therefore we will
    ernestafy this basin.
    """
    if output == None:
        output = './output'
        if not os.path.isdir(output):
            os.mkdir(output)

    # Output files
    imgs = {
            'dem':demfile,
            'filled': os.path.join(output,'filled.tif'),
            'flow_dir': os.path.join(output,'flow_dir.tif'),
            'slope': os.path.join(output,'slope.tif'),
            'drain_area': os.path.join(output,'drain_area.tif'),
            'basin_drain_area': os.path.join(output,'basin_drain_area.tif'),
            'thresh_streams':os.path.join(output,'streams_thresh_{}.tif'.format(threshold)),
            'corrected_points': os.path.join(output,'on_stream_points.shp'),
            'thresh_basin_streams':os.path.join(output,'basin_streams_thresh_{}.tif'.format(threshold)),
            'order':os.path.join(output,'stream_order_thresh_{}.tif'.format(threshold)),
            'tree':os.path.join(output,'treefile_thresh_{}.tif'.format(threshold)),
            'coord':os.path.join(output,'coordfile_thresh_{}.tif'.format(threshold)),
            'net':os.path.join(output,'netfile_thresh_{}.tif'.format(threshold)),
            'watersheds':os.path.join(output,'wfile_thresh_{}.tif'.format(threshold))
            }

    # 1. Pit Remove in order to fill the pits in the DEM
    pitremove(imgs['dem'], outfile=imgs['filled'])

    # 2. D8 Flow Directions in order to compute the flow direction in each DEM cell
    calcD8Flow(imgs['filled'], d8dir_file=imgs['flow_dir'], d8slope_file=imgs['slope'])

    # 3. D8 Contributing Area so as to compute the drainage area in each DEM cell
    calcD8DrainageArea(imgs['flow_dir'], areaD8_out=imgs['drain_area'])

    # 4. Stream Definition by Threshold, in order to extract a first version of the stream network
    defineStreamsByThreshold(imgs['drain_area'],
                             threshold_streams_out=imgs['thresh_streams'],
                             threshold=1000)

    # 5. Move Outlets to Streams, so as to move the catchment outlet point on one of the DEM cells
    #    identified by TauDEM as belonging to the stream network
    outlets_2_streams(imgs['flow_dir'], imgs['thresh_streams'], pour_points,
                                       new_pour_points=imgs['corrected_points']) #?????????? Should this be the outlet only or all the points
    # 6. D8 Contributing Area again, but with the catchment outlet point as additional input data
    calcD8DrainageAreaBasin(imgs['flow_dir'], imgs['corrected_points'],
                                         areaD8_out=imgs['basin_drain_area'])

    # 7. Stream Definition by Threshold again, but with the catchment outlet point as additional input data
    defineStreamsByThreshold(imgs['basin_drain_area'],
                             threshold_streams_out=imgs['thresh_basin_streams'],
                             threshold=1000)

    # 8. Stream Reach And Watershed
    delineate_streams(imgs['dem'], imgs['flow_dir'], imgs['basin_drain_area'],
                       imgs['thresh_basin_streams'], imgs['corrected_points'],
                       stream_orderfile=imgs['order'], treefile=imgs['tree'],
                       coordfile=imgs['coord'], netfile=imgs['net'],
                       wfile=imgs['watersheds'])


def convert2ascii(infile, outfile=None):
    """
    Convert to ascii
    """
    check_path(infile)
    check_path(outfile,outfile=True)

    # convert wfile files to ascii
    CMD = 'gdal_translate -of AAIGrid {0} {1}'.format(infile,outfile)
    action = get_docker_bash() + CMD
    run_cmd(action)


def main():

    p = argparse.ArgumentParser(description='Delineate a new basin for SMRF/AWSM/Streamflow.')

    p.add_argument("-d","--dem", dest="dem",
                    required=True,
                    help="Path to dem")
    p.add_argument("-p","--pour", dest="pour_points",
                    required=True,
                    help="Path to a .bna of pour points")
    p.add_argument("-bo","--basin_outlet", dest="basin_outlet",
                    required=True,
                    help="Path to a .bna of the basin outlet")
    p.add_argument("-o","--output", dest="output",
                    required=False,
                    help="Path to output folder")
    p.add_argument("-t","--threshold", dest="threshold",
                    nargs="+",
                    help="Thresholds to use for defining streams, default=1000")
    p.add_argument("-n","--nthreads", dest="nthreads",
                    required=False,
                    help="cores to use when processing the data")
    p.add_argument("-re","--rerun", dest="rerun",
                    required=False, action='store_true',
                    help="Boolean Flag that determines whether to run the "
                         "script from the beginning or assume that the flow "
                         "accumulation has been completed once")

    args = p.parse_args()

    ernestafy(args.dem,args.pour_points)

if __name__ == '__main__':
    main()
