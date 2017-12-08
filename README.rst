BASIN SETUP TOOL v0.1.0
=======================
The basin setup tool is designed to create the required inputs for running
SMRF and AWSM. The tool outputs a netcdf file containing:

* Basin mask
* Basin DEM
* Basin Vegetation type (From NLCD)
* Basin Vegetation Height (From Landfire)
* Basin Vegetaiton 

INSTALL
-------
To install the utility so that it is usable everywhere in the command line:

sudo make install


USAGE
-----
basin_setup -f rme_basin_outline.shp -dm ~/Downloads/ASTGTM2_N43W117/ASTGTM2_N43W117_dem.tif
