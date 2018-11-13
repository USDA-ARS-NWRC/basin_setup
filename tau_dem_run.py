import argparse
import numpy as np
import pandas as pd
import os
from subprocess import Popen, PIPE
import sys
from basin_setup import Messages

DEBUG=True
out = Messages()

def check_path(filename, outfile=False):
    """
    Checks whether an file has been provided exists.
    If outfile is true then we assume we are making a file and there fore we
    should only check if the directory exists.

    Args:
        filename: path to a file
        outfile: Boolean indicating whether to check for a file (outfile=False)
                 or a directory
    """
    folder = os.path.basename(filename)

    if outfile and not os.path.isdir(folder):
        out.error("Output directory does not exist!\n{}".format(filename))
        sys.exit()

    if not outfile and not os.path.isfile(filename):
        out.error("Input file does not exist!\n{}".format(filename))
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
                  "Attempted to rename:" {0}.format(original))
        sys.exit()

    p = path[0]+"_{}".format(add_tag)_path[-1]

def run_cmd(cmd):
    """
    Executes the command and pipes the output to the console.
    Args:
        cmd: String command to be entered in the the command prompt
    """

    out.info('Running {}'.format(cmd))
    s = Popen(cmd, shell=True, stdout=PIPE)

    while True:
        line = s.stdout.readline()
        out.info(line)
        if not line:
            break


def get_docker_bash(nthreads=None):
    """
    Returns the string command for running in a docker.
    """
    # make entrypoint take in the tau commands call
    action = 'docker run --rm -ti quay.io/wikiwatershed/taudem'
         ' -v $(pwd):/home --entrypoint /bin/bash '

    # Added in threaded business
    if nthreads != None:
        action+='mpiexec -n {0} '.format(nthreads)

    return action


def pitremove(demfile, outfile=None):
    """
    STEP #1
    Builds the command to pit fill the DEM and executes it.

    Args:
        demfile: Path to tif of the DEM.
        outfile: Path to write the pit filled DEM.
    """
    action = get_docker_cmd()

    if outfile == None:
        demfile.split('.')[0] + "_filled.tif"

    check_path(demfile)
    check_path(outfile, outfile=True)

    action += " --entrypoint /bin/bash pitremove -z {0} -fel {1}"
            "".format(demfile, out_file)

    run_cmd(action)


def calcD8Flow(filled_dem, d8dir_file=None, d8slope_file=None):
    """
    STEP #2
    Builds the command to calculate the D8 flow for the flow directionand
    executes it.

    Args:
        filled_dem: Path to tif of the pit filled DEM.
        d8dir_file: Path to write the D8 flow direction.
        d8slope_file: Path to write the D8 flow slope.
    """
    action = get_docker_cmd()


    check_path(filled_dem)
    check_path(d8dir_file, outfile=True)
    check_path(d8slope_file, outfile=True)

    CMD = "d8flowdir -fel ${0} -p ${1} -sd8 ${2}".format(filled_dem,
                                                         d8dir_file,
                                                         d8flowdir)
    action = get_docker_cmd()
    action += CMD
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
    CMD = "aread8 -p ${0} -ad8 ${1}".format(d8flowdir,areaD8_out)
    action = get_docker_bash() + CMD
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
    check_path(threshold_out,outfile=True)

    CMD="mpiexec -n 8 threshold -ssa ${0} -src ${1} -thresh {2}".format(
                                                                areaD8,
                                                                threshold_out,
                                                                threshold)
    action = get_docker_bash() + CMD
    run_cmd(action)


def outlets2_streams(d8flowdir, threshold_streams, pour_points,
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
    action = get_docker_bash() + CMD
    run_cmd(action)


def calcD8DrainageAreaBasin(d8flowdir, basin_outlets, basin_outlets_moved=None):
    """
    STEP #6
    D8 Contributing Area again, but with the catchment outlet point as
    additional input data
    """
    check_path(d8flowdir)
    check_path(basin_outlets)
    check_path(basin_outlets_moved, outfile=True)

    CMD = 'aread8 -p {0} -ad8 {1}.tif -o {2}'.format(d8flowdir,basin_outlets,
                                                            basin_outlets_moved)
    action = get_docker_bash() + CMD
    run_cmd(action)


def delineate_streams(dem, d8flowdir, pour_points, aread8, threshold_streams,
                      basin_outlets, stream_orderfile=None, treefile=None,
                      coordfile=None, netfile=None,wfile=None):
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
    # Check path validity
    inputs = [dem, d8flowdir, pour_points, aread8, threshold_streams,
              basin_outlets]

    outputs = [stream_orderfile, treefile, coordfile, netfile, wfile]
    for f in inputs:
        check_path(f)

    for f in outputs:
        check_path(f, outfile=True)

    CMD = 'streamnet -fel {0} -p {1} -ad8 {2} -src{3} -ord {4} -tree {5}'
                     '-coord {6} -net {7} -o {8} -w {9}'.format(
                                                            dem,
                                                            d8flowdir,
                                                            aread8,
                                                            threshold_streams,
                                                            stream_orderfile,
                                                            treefile,
                                                            coordfile,
                                                            netfile,
                                                            basin_outlets_moved,
                                                            wfile)
    action = get_docker_bash() + CMD
    run_cmd(action)

def ernestafy(demfile,output=None):
    """
    Run TauDEM using the script Ernesto Made.... therefore we will
    ernestafy this basin.
    """

    # 1. Pit Remove in order to fill the pits in the DEM
    pitremove()

    # 2. D8 Flow Directions in order to compute the flow direction in each DEM cell
    calcD8Flow(filled_dem, d8dir_file=None, d8slope_file=None)

    # 3. D8 Contributing Area so as to compute the drainage area in each DEM cell
    calcD8DrainageArea(d8flowdir, areaD8_out=None):

    # 4. Stream Definition by Threshold, in order to extract a first version of the stream network
    defineStreamsByThreshold(areaD8, threshold_streams_out=None, threshold=1000):

    # 5. Move Outlets to Streams, so as to move the catchment outlet point on one of the DEM cells
    #    identified by TauDEM as belonging to the stream network
    outlets2_streams(d8flowdir, threshold_streams, pour_points,
                                                   new_pour_points=None)
    # 6. D8 Contributing Area again, but with the catchment outlet point as additional input data
    calcD8DrainageAreaBasin(d8flowdir, basin_outlets, basin_outlets_moved=None):

    # 7. Stream Definition by Threshold again, but with the catchment outlet point as additional input data
    defineStreamsByThreshold(areaD8, threshold_streams_out=None, threshold=1000):

    # 8. Stream Reach And Watershed
    delineate_streams(dem, d8flowdir, pour_points, aread8, threshold_streams,
                          basin_outlets, stream_orderfile=None, treefile=None,
                          coordfile=None, netfile=None,wfile=None)


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

    p = argparse.ArgumentParser(description='Delineate a new basin for SMRF/AWSM.')'

    p.add_argument('-d','--dem', dest='dem',
                    required=True,
                    help="Path to dem)
    pitremove(args.dem)
