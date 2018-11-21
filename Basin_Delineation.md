# Using the Delineate Script

## Installation
```
 $ sudo apt-get install mpich
```

* Install TauDem, download the source from github.
* Copy over the binaries to a folder that is seen by a PATH
* Install GDAL, ensure that you have python and netcdf libs too.
* Install the scripts from basin setup

## Delineate
* Get a DEM in the smallest version possible without losing any of your basin
* Obtain pour points in which the primary id is an identifiable name
* Run the command to delineate:
```
delineate -d examples/delineate_tollgate/topo_50m.tif -p examples/delineate_tollgate/tollgate_xyz.bna
``` 

The above command will create a wide degree of files. Namely it will create shapefiles for the whole basin and subbasin that contains a pour point

