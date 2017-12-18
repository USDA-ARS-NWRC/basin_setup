BASIN SETUP TOOL v0.1.0
=======================
The basin setup tool is a python script designed to create the required inputs for running
SMRF_ and AWSM_ simulations. The tool outputs a single netcdf file containing:

.. _SMRF: https://smrf.readthedocs.io/en/develop/
.. _AWSM: https://github.com/USDA-ARS-NWRC/AWSM


* Basin mask
* Basin DEM
* Basin Vegetation type (From NLCD)
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
To compile from source follow the instructions provided at :

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


USAGE
-----
To use basin_setup you only need a shapefile of your basins boundary and a dem that contains the 
the extents of the shapefile. **It is required that the shapefile is in UTM.**. The projection of
the DEM wil be converted to that of the shapefile.

To use basin_setup at it's simplest form, just provide a shapefile and dem:

.. code-block:: bash

	$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif

To specify the cell size use the  cellsize flag which is specified in meters, if it is not used the default is 50m:

.. code-block:: bash

	$  basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif -- cell_size 10



