# BASIN SETUP TOOL v0.14.6
[![PyPI version fury.io](https://badge.fury.io/py/ansicolortags.svg)](https://pypi.python.org/basin_setup/ansicolortags/)
[![Docker Build Status](https://img.shields.io/docker/build/usdaarsnwrc/basin_setup.svg)](https://hub.docker.com/r/usdaarsnwrc/basin_setup/)
[![Travis Tests](https://travis-ci.com/USDA-ARS-NWRC/basin_setup.svg?branch=master)](https://travis-ci.com/USDA-ARS-NWRC/basin_setup)

The basin setup tools is a set of CLI tools designed to create the required
inputs for running [SMRF](https://smrf.readthedocs.io/en/develop/) and
[AWSM](https://github.com/USDA-ARS-NWRC/AWSM) snow simulations and GIS projects


# Package Features
There are 6 commands that come with basin setup

1. [delineate](#delineate) - Automatically delineates a new basin given a pour_points file and a DEM.
2. [basin_setup](#basin\_setup) - Creates all the images in a single netcdf for running SMRF/AWSM, often referred to as the topo.nc
3. [grm](#grm) - Aggregates Lidar snow depths into a single netcdf.
4. [make_qgis_proj](#make_qgis_proj) - Adds files to a xml file to be used in QGIS
5. [make_dem_colormap](#Making-Colormaps) - Makes a custom colormap for a dem specifically making nice maps
6. [make_veg_type_colormap](#Making-Colormaps) - Makes a custom colormap from the landfire data set specifically for maps


# Getting These Tools

## Using Docker
Building GDAL can sometimes be a headache if you are unfamiliar with
normal build practices. If you would like to just use the tool with no
questions asked, then use the docker command. However note that the file
structure is what is represented inside the docker. So you must mount
local directories to docker ones fortunately we have created a data
folder for you to do just that. Mounting these will also ensure files
you generate persist.

The commands listed in this README are used the same but with
extra:

``` bash
$ docker run -it --rm  --entrypoint <COMMAND> -v $(pwd):/data -v <DOWNLOADS>/:/data/downloads usdaarsnwrc/basin_setup <ARGS>
```

The command above is performing the following:

  - Mounting the current working directory to the ```/data``` folder
    inside docker (linux only, otherwise use absolute paths)
  - Mounting the current working directory to the
    ```/data/downloads``` folder inside docker
  - Running the COMMAND with the ARGS

## Install From Source

**Prequisites**:

  - GDAL 2.3.2
  - Ubuntu 16.04, 18.04
  - Python\>=3.5
  - pip 19.2.1

To begin the install for basin\_setup, ensure that GDAL is compiled from
source. Note: Do not install the python library for GDAL but rather the
command line utiltiies. To compile from source follow the instructions
provided at:

<http://trac.osgeo.org/gdal/wiki/BuildHints>

Once GDAL is installed, install the python requirements create a virtualenv
using python3:

```bash

$ virtualenv -p python3 basinenv
$ source basinenv/bin/activate

```

``` bash
$ pip install -r requirements.txt
```

Finally to install basin\_setup for commandline use use:

``` bash
$ python install setup.py
```

If you want to develop on basin\_setup use the following command to
install the utility so that you changes to the source will be used
without having to reinstall

``` bash
$ python setup.py develop
```

# Commands

----
## delineate
----

The delineation script automatically delineates a basin using pour points and
a dem. The tool simply wraps the tools from [TaudDEM](http://hydrology.usu.edu/taudem/taudem5/index.html)
and streamlines the process.

The script will produce shapefiles of all the subbasins using a threshold(s).
It also saves data to allow for re-running faster.

#### Features

* Auto basin delineation.
* Multiruns with multiple thresholds.
* Rerun functionality to reduce computation time.
* Outputs Shapefiles for basins and subbasins
* Runs in parallel

#### General Usage

* Pour points must be in a BNA format. The name of the points in the BNA file
  will be used as the name for the output files.
* DEM must be a .tif
* Threshold is the number of cells that would drain through a single pour point, the smaller the number the more subbasins.

``` bash
$ delineate -p pour_points.bna -d dem.tif --rerun -t 2000000 -n 2 --debug
```

Using the debug flag will leave lots of extra files that were generated on the
way in a folder named delineation

To get files necessary for streamflow add --streamflow flag to the command which will
preserve streamflow files like reaches and tree files.


----
## basin\_setup
----
The basin_setup
outputs a single netcdf file containing:

 - Basin mask
 - Basin DEM
 - Basin Vegetation type (From Landfire)
 - Basin Vegetation Height (From Landfire)
 - Basin Vegetation Tau (radiation parameters)
 - Basin Vegetation K(radiation parameters)
 -
#### General Usage

To use basin\_setup you only need a shapefile of your basins boundary
and a dem that contains the the extents of the shapefile. **It is
required that the shapefile is in UTM.** The projection of the DEM wil
be converted to that of the shapefile.

To use basin\_setup at it's simplest form, just provide a shapefile and
dem:

**Easiest Use**

``` bash
$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif
```

**Custom Cell Size** To specify the cell size use the cellsize flag
which is specified in meters, if it is not used the default is
50m:

``` bash
$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif --cell_size 10
```

**Switching Array Origin**

Occasionally an image will have the correct coordinates and orientation
but its array will have a different origin than expected. This can
happen when alternating between raster images and other data sets. For
example, using the commands above will produce successful topo.nc for
SMRF and will display correctly when using something like ncview (which
considers the x and y data inputted). However if you were to simply plot
with imshow from matplotlib that data you will find is upside down, so
the default behavior flips the image. This is because of a difference in
array origins. To not flip this use the ```--noflip``` flag which flips
the y axis data and the images over the x-axis resulting images
correctly oriented in ncview and
imshow.

``` bash
$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif --noflip
```
#### Setting Up Point Models

It is possible to create what our group considers a point model. The
goal here is to create all the files necessary to run in SMRF/AWSM
without having to change the SMRF/AWSM code to test the modeling system
on a point. This means creating the smallest sized topo possible. In
this case thats a 3X3 image. NetCDF dictates an image cannot be 1 pixel.
Below is the simplest way to create a point model for Reynolds Mountain
East's snow pillow site.

**Easiest Use**

``` bash
$  basin_setup -p 519976,4768323 -dm ASTGTM2_N43W117_dem.tif --epsg 2153
```

Note: Until this code is improved the user must provided the EPSG code
so the projection information can be obtained. If you are not sure what
your EPSG is use this link to find it.
<http://spatialreference.org/ref/epsg/>

With a point model there is sometimes the desire to use a uniform value
for variables. This is done by using the uniform flag.

**Uniform Data**

``` bash
$  basin_setup -p 519976,4768323 -dm ASTGTM2_N43W117_dem.tif --epsg 2153 --uniform
```

Which simply picks the middle cell and applies it everywhere. On this
same idea the DEM can be provided as a single value. So the user can
choose a different elevation than what an image can provide. E.g.

**Custom DEM**

``` bash
$  basin_setup -p 519976,4768323 -dm 1000 --epsg 2153 --uniform
```

----
## grm
----

The GRM tool aggregates lidar geotiffs into a single netcdf for each water year.
The images are stored in time according to hours from the 10-01-YYYY

#### Features

* Add any number Lidar geotiffs in a single command.
* Append any number of lidar geotifs to an existing lidar netcdf
* Autodetect dates for images filenames containing date format YYYYMMDD
* Reprojects, resize, resample, and crop domains according to the topo.nc
* Assign nan values where -9999 or nans were provided.
* Check netcdf features to insure overwriting previous images data fidelity
* Manually pass in dates

#### General Usage

The following will generate a netcdf named lidar_depths_wy2020.nc with two
flights stored at 4-11-2020 and 4-15-2020 as determined by the image filenames.

```bash
grm -t topo.nc -i 20200411_SuperDepths.tif 20200415_superDepths.tif -b lakes
```

----
## make_qgis_proj
----

Script builds a .qgs file for opening in QGIS. The templates are built on QGIS 2.17
but have worked in 3.4 and more. The script makes the projects assuming you're
examining delineations.

#### Features

* Command accepts geotifs, shapefiles, BNA point files, multi-image netcdf
* Use keywords in your filenames to assign colormaps to streams, points, DEM, hillshades and veg data.
* Select specific netcdf variables to add, key words here also apply the same colormaps

#### General Usage

* Pour points must be in a BNA format. The name of the points in the BNA file
  will be used as the name for the output files.
* DEM must be a .tif
* Threshold is the number of cells that would drain through a single pour point, the smaller the number the more subbasins.

``` bash
$ 	make_qgis_proj -t veg_type.tif dem.tif ./dem/hillshade.tif \
										-s pour_points.bna \
                    ./delineation/basin_outline.shp \
										./delineation/streamflow/thresh_10000/net_thresh_10000.shp
										-n basin_setup/topo.nc \
										-v veg_type dem \
										--epsg 32611
```

The result will be a file named setup.qgs which can be opened in QGIS.

**NOTE:**  Colormaps can be added to a folder in the same path of execution
titled colormaps.

----
## Making Colormaps
----

There are two scripts for making colormaps.
1. make_dem_colormap - Makes a custom, map quality colormap based on DEM
2. make_veg_type_colormap - Makes a custom, map quality colormap for Landfire veg types (Water is blue, forest is green, bare is brown, snow/ice is white, grass is light green)

#### Features

* Command accepts geotifs, shapefiles, BNA point files, multi-image netcdf
* Use keywords in your filenames to assign colormaps to streams, points, DEM, hillshades and veg data.
* Select specific netcdf variables to add, key words here also apply the same colormaps

#### General Usage

``` bash
make_dem_colormap dem.tif
make_veg_type_colormap  ~/Downloads/US_140EVT_20180618/
```

Both of these will produce a .qml and put it in a folder caller colormaps in the
same directory this runs.
