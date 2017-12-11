BASIN SETUP TOOL v0.1.0
=======================
The basin setup tool is a python script designed to create the required inputs for running
SMRF and AWSM. The tool outputs a netcdf file containing:

* Basin mask
* Basin DEM
* Basin Vegetation type (From NLCD)
* Basin Vegetation Height (From Landfire)
* Basin Vegetaiton 

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

pip install -r requirements.txt

Finally to install basin_setup for commandline use use:

sudo make install

If you want to develop on basin_setup use the following command to install the utility
so that you changes to the source will be used without having to reinstall

sudo make develop


USAGE
-----
basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif
