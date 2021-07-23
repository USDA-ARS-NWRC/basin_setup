# Basin Setup Tools

The basin setup tools is a set of CLI tools designed to create the required inputs for running [SMRF](https://smrf.readthedocs.io/en/develop/) and [AWSM](https://github.com/USDA-ARS-NWRC/AWSM) snow simulations.

1. [delineate](#delineate) - Automatically delineates a new basin given a pour_points file and a DEM.
2. [generate_topo](#generate\_topo) - Creates all the images in a single netcdf for running SMRF/AWSM, often referred to as the topo.nc
3. [grm](#grm) - Aggregates Lidar snow depths into a single netcdf.

- [Basin Setup Tools](#basin-setup-tools)
  - [Getting These Tools](#getting-these-tools)
    - [Using Docker](#using-docker)
    - [Install From Source](#install-from-source)
  - [Commands](#commands)
    - [**delineate**](#delineate)
      - [Features](#features)
      - [General Usage](#general-usage)
    - [**generate\_topo**](#generate_topo)
      - [General Usage](#general-usage-1)
    - [**grm**](#grm)
      - [Features](#features-1)
      - [General Usage](#general-usage-2)

## Getting These Tools

### Using Docker

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
docker run -it --rm  --entrypoint <COMMAND> -v $(pwd):/data usdaarsnwrc/basin_setup <ARGS>
```

The command above is performing the following:

- Mounting the current working directory to the ```/data``` folder
 inside docker (linux only, otherwise use absolute paths)
- Running the COMMAND with the ARGS

### Install From Source

**Prequisites**:

- GDAL 2.3.2
- Ubuntu 16.04, 18.04
- Python\>=3.5
- pip 19.2.1

To begin the install for ``basin\_setup``, ensure that GDAL is compiled from
source. Note: Do not install the python library for GDAL but rather the
command line utiltiies. To compile from source follow the instructions
provided at:

<http://trac.osgeo.org/gdal/wiki/BuildHints>

Once GDAL is installed, install the python requirements create a virtualenv
using python3:

```bash
virtualenv -p python3 basinenv
source basinenv/bin/activate
```

``` bash
pip install -r requirements.txt
```

Finally to install basin\_setup for commandline use use:

``` bash
python install setup.py
```

If you want to develop on basin\_setup use the following command to
install the utility so that you changes to the source will be used
without having to reinstall

``` bash
python setup.py develop
```

## Commands

### **delineate**

The delineation script automatically delineates a basin using pour points and a dem. The tool simply wraps the tools from [TaudDEM](http://hydrology.usu.edu/taudem/taudem5/index.html) and streamlines the process.

The script will produce shapefiles of all the subbasins using a threshold(s). It also saves data to allow for re-running faster.

#### Features

- Auto basin delineation.
- Multiruns with multiple thresholds.
- Rerun functionality to reduce computation time.
- Outputs Shapefiles for basins and subbasins
- Runs in parallel

#### General Usage

- Pour points must be in a BNA format. The name of the points in the BNA file
  will be used as the name for the output files.
- DEM must be a .tif
- Threshold is the number of cells that would drain through a single pour point, the smaller the number the more subbasins.

``` bash
delineate -p pour_points.bna -d dem.tif --rerun -t 2000000 -n 2 --debug
```

Using the debug flag will leave lots of extra files that were generated on the
way in a folder named delineation

To get files necessary for streamflow add --streamflow flag to the command which will
preserve streamflow files like reaches and tree files.

### **generate\_topo**

Outputs a single netcdf file containing:

- Basin mask
- Basin DEM
- Basin Vegetation type (From Landfire)
- Basin Vegetation Height (From Landfire)
- Basin Vegetation Tau (radiation parameters)
- Basin Vegetation K (radiation parameters)
- Subbasin masks (optional)

#### General Usage

To use ``generate_topo`` you only need

- A shapefile of your basins boundary in UTM (from ``delineate``). This will become the projections for the ``topo.nc``
- A dem that contains the the extents of the shapefile
- Downloaded [Landfire 1.4.0](https://landfire.gov/version_download.php) EVT and EVH datasets

``generate_topo`` uses a configuration file to specify all the required parameters to run. See the [CoreConfig](basin_setup/CoreConfig.ini) for options and the [sample configuration files](tests/Lakes/config.ini).

``` bash
basin_setup config.ini
```

### **grm**

The GRM tool aggregates lidar geotiffs into a single netcdf for each water year. The images are stored in time according to hours from the 10-01-YYYY

#### Features

- Add any number Lidar geotiffs in a single command.
- Append any number of lidar geotifs to an existing lidar netcdf
- Autodetect dates for images filenames containing date format YYYYMMDD
- Reprojects, resize, resample, and crop domains according to the topo.nc
- Assign nan values where -9999 or nans were provided.
- Check netcdf features to insure overwriting previous images data fidelity
- Manually pass in dates

#### General Usage

The following will generate a netcdf named lidar_depths_wy2020.nc with two
flights stored at 4-11-2020 and 4-15-2020 as determined by the image filenames.

```bash
grm -t topo.nc -i 20200411_SuperDepths.tif 20200415_superDepths.tif -b lakes
```
