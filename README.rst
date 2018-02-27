BASIN SETUP TOOL v0.2.1
=======================
The basin setup tool is a python script designed to create the required inputs for running
SMRF_ and AWSM_ simulations. The tool outputs a single netcdf file containing:

.. _SMRF: https://smrf.readthedocs.io/en/develop/
.. _AWSM: https://github.com/USDA-ARS-NWRC/AWSM


* Basin mask
* Basin DEM
* Basin Vegetation type (From Landfire)
* Basin Vegetation Height (From Landfire)
* Basin Vegetation Tau
* Basin Vegetation K


INSTALL
-------

**Prequisites**:

* GDAL 2.2.0
* Python 2.7.13
* pip 9.0.1

To begin the install for basin_setup, ensure that GDAL is compiled from source.
Note: Do not install the python library for GDAL but rather the command line utiltiies.
To compile from source follow the instructions provided at:

http://trac.osgeo.org/gdal/wiki/BuildHints

Once GDAL is installed, install the python requirements using pip:

.. code-block:: bash

	$ pip install -r requirements.txt

Finally to install basin_setup for commandline use use:

.. code-block:: bash

	$ sudo make install

If you want to develop on basin_setup use the following command to install the utility
so that you changes to the source will be used without having to reinstall

.. code-block:: bash

	$ sudo make develop


GENERAL USAGE
-------------
To use basin_setup you only need a shapefile of your basins boundary and a dem that contains the
the extents of the shapefile. **It is required that the shapefile is in UTM.** The projection of
the DEM wil be converted to that of the shapefile.

To use basin_setup at it's simplest form, just provide a shapefile and dem:

**Easiest Use**

.. code-block:: bash

	$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif

To specify the cell size use the  cellsize flag which is specified in meters, if it is not used the default is 50m:

**Custom Cell Size**

.. code-block:: bash

	$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif --cell_size 10

Point Models
------------
It is possible to create what our group considers a point model. The goal here
is to create all the files necessary to run in SMRF/AWSM without having to
change the SMRF/AWSM code to test the modeling system on a point. This means
creating the smallest sized topo possible. In this case thats a 3X3 image.
NetCDF dictates an image cannot be 1 pixel. Below is the simplest way to create
a point model for Reynolds Mountain East's snow pillow site.

**Easiest Use**

.. code-block:: bash

	$  basin_setup -p 519976,4768323 -dm ASTGTM2_N43W117_dem.tif --epsg 2153

Note: Until this code is improved the user must provided the EPSG code so the
projection information can be obtained. If you are not sure what your EPSG is
use this link to find it. http://spatialreference.org/ref/epsg/

With a point model there is sometimes the desire to use a uniform value for
variables. This is done by using the uniform flag.

**Uniform Data**

.. code-block:: bash

	$  basin_setup -p 519976,4768323 -dm ASTGTM2_N43W117_dem.tif --epsg 2153 --uniform

Which simply picks the middle cell and applies it everywhere.  On this same idea
the DEM can be provided as a single value. So the user can choose a different elevation
than what an image can provide. E.g.

**Custom DEM**

.. code-block:: bash

	$  basin_setup -p 519976,4768323 -dm 1000 --epsg 2153 --uniform
