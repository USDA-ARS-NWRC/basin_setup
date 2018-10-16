# BASIN SETUP TOOL v0.4.0

[![Docker Build Status](https://img.shields.io/docker/build/usdaarsnwrc/basin_setup.svg)](https://hub.docker.com/r/usdaarsnwrc/basin_setup/)

The basin setup tool is a python script designed to create the required
inputs for running [SMRF](https://smrf.readthedocs.io/en/develop/) and
[AWSM](https://github.com/USDA-ARS-NWRC/AWSM) simulations. The tool
outputs a single netcdf file containing:

  - Basin mask
  - Basin DEM
  - Basin Vegetation type (From Landfire)
  - Basin Vegetation Height (From Landfire)
  - Basin Vegetation Tau
  - Basin Vegetation K

## INSTALL

**Prequisites**:

  - GDAL 2.3.1
  - Python\>=3.5
  - pip 9.0.1

To begin the install for basin\_setup, ensure that GDAL is compiled from
source. Note: Do not install the python library for GDAL but rather the
command line utiltiies. To compile from source follow the instructions
provided at:

<http://trac.osgeo.org/gdal/wiki/BuildHints>

Once GDAL is installed, install the python requirements using pip:

```
$ pip install -r requirements.txt
```

Finally to install basin\_setup for commandline use use:

```
$ sudo make install
```

If you want to develop on basin\_setup use the following command to
install the utility so that you changes to the source will be used
without having to reinstall

```
$ sudo make develop
```

## GENERAL USAGE

To use basin\_setup you only need a shapefile of your basins boundary
and a dem that contains the the extents of the shapefile. **It is
required that the shapefile is in UTM.** The projection of the DEM wil
be converted to that of the shapefile.

To use basin\_setup at it's simplest form, just provide a shapefile and
dem:

**Easiest Use**

```
$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif
```

**Custom Cell Size** To specify the cell size use the cellsize flag
which is specified in meters, if it is not used the default is
50m:

```
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

```
$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif --noflip
```
# Point Models

It is possible to create what our group considers a point model. The
goal here is to create all the files necessary to run in SMRF/AWSM
without having to change the SMRF/AWSM code to test the modeling system
on a point. This means creating the smallest sized topo possible. In
this case thats a 3X3 image. NetCDF dictates an image cannot be 1 pixel.
Below is the simplest way to create a point model for Reynolds Mountain
East's snow pillow site.

**Easiest Use**

```
$  basin_setup -p 519976,4768323 -dm ASTGTM2_N43W117_dem.tif --epsg 2153
```

Note: Until this code is improved the user must provided the EPSG code
so the projection information can be obtained. If you are not sure what
your EPSG is use this link to find it.
<http://spatialreference.org/ref/epsg/>

With a point model there is sometimes the desire to use a uniform value
for variables. This is done by using the uniform flag.

**Uniform
Data**

```
$  basin_setup -p 519976,4768323 -dm ASTGTM2_N43W117_dem.tif --epsg 2153 --uniform
```

Which simply picks the middle cell and applies it everywhere. On this
same idea the DEM can be provided as a single value. So the user can
choose a different elevation than what an image can provide. E.g.

**Custom DEM**

```
$  basin_setup -p 519976,4768323 -dm 1000 --epsg 2153 --uniform
```

# Using it in Docker

Building GDAL can sometimes be a headache if you are unfamiliar with
normal build practices. If you would like to just use the tool with no
questions asked, then use the docker command. However note that the file
structure is what is represented inside the docker. So you must mount
local directories to docker ones fortunately we have created a data
folder for you to do just that. Mounting these will also ensure files
you generate persist.

The commands are used the same but with
extra:

```
$ docker run -it --rm -v $(pwd):/data -v <DOWNLOADS>/:/data/downloads usdaarsnwrc/basin_setup:develop -f SHAPEFILE -dm DME_IMG -d /data/downloads
```

The command above is:

  - Mounting the current working directory to the ```/data``` folder
    inside docker
  - Mounting the current working directory to the
    ```/data/downloads``` folder inside docker
  - Running basin_setup with the dowloads pointing to the docker side.
