=======
History
=======

0.1.0 (2017-12-05)
------------------

* Project Inception!

0.2.0 (2018-02-17)
------------------

* documentation
* point model setup
* cell size bug fix 1_

.. _1: https://github.com/USDA-ARS-NWRC/basin_setup/issues/1


0.3.0 (2018-09-07)
------------------

* Array flipping option
* improved documentation
* Python 3 compatibility
* output unique veg values being used
* Dockerfile!!

0.4.0 (2017-10-16)
------------------

* Projection Information added
* Project metdata and badges

0.6.0 (2018-11-14)
------------------

* Fixes for 8_ and 9_
* Updated Requirements
* Added Makefile for installing
* Prototype for a delineation script!

.. _8: https://github.com/USDA-ARS-NWRC/basin_setup/issues/8
.. _9: https://github.com/USDA-ARS-NWRC/basin_setup/issues/9


0.7.0 (2018-11-21)
------------------

* Fixed Spelling errors in file management for delineate
* Exanded delineate shapefile output including subassins
* Improved documentation for delineate
* Auto determining the projection info

0.8.0 (2019-03-06)
------------------

* Fixes for 12_, 15_, 16_, 17_, 18_
* Data provenance work for delineate
* Improvements to docker build
* Output expanded in delineate for files required for Streamflow
* Extracted functionality and moved to spatialnc
* Added GRM tool for aggregating lidar flights into a netcdf from ASO

.. _12: https://github.com/USDA-ARS-NWRC/basin_setup/issues/12
.. _15: https://github.com/USDA-ARS-NWRC/basin_setup/issues/15
.. _16: https://github.com/USDA-ARS-NWRC/basin_setup/issues/16
.. _17: https://github.com/USDA-ARS-NWRC/basin_setup/issues/17
.. _18: https://github.com/USDA-ARS-NWRC/basin_setup/issues/18


0.9.0 (2019-07-18)
------------------

* Fixes for 27_
* Working on NaN assignments
* Expanded resampling techniques for GRM

.. _27: https://github.com/USDA-ARS-NWRC/basin_setup/issues/27


0.10.0 (2019-07-18)
------------------
* Fixes for 24_
* Added in Static file output fro ARS streamflow modeling
* Documentation Improvements
.. _24: https://github.com/USDA-ARS-NWRC/basin_setup/issues/24


0.11.0 (2019-08-09)
------------------
* Fixes for 31_
* First Release on Pypi
* Converted Basin_setup to a python package not a collection of scripts
* Vegetation Parameter requirements more strict, requiring a csv to dictate the interpretation
* Updated Docker

.. _31: https://github.com/USDA-ARS-NWRC/basin_setup/issues/31


0.12.0 (2019-09-16)
------------------
* Fixes for 34_
* Added in CLI extents flag for cutting exactly to a known domain.
* Added resampling to DEM and Veg Height layers, all else use nearest neighbor.

.. _34: https://github.com/USDA-ARS-NWRC/basin_setup/issues/34


0.13.0 (2019-12-23)
-------------------
* Fixes for 29_, 36_, 37_, 39_, 40_
* Added in a bypass flag for skipping over missing tau/k data
* Updated veg tau/k parameters
* Added tif file format to parse_extent
* Added first unittests!

.. _29: https://github.com/USDA-ARS-NWRC/basin_setup/issues/29
.. _36: https://github.com/USDA-ARS-NWRC/basin_setup/issues/36
.. _37: https://github.com/USDA-ARS-NWRC/basin_setup/issues/37
.. _39: https://github.com/USDA-ARS-NWRC/basin_setup/issues/39
.. _40: https://github.com/USDA-ARS-NWRC/basin_setup/issues/40


0.14.0 (2020-02-11)
-------------------
* Fixes for 41_, 42_, 43_, 44__, 45__
* Added in colormap making scripts
* Added in QGIS project maker script
* Added in a script for adding veg values to landfire dataset
* Added values in the landfire vegetation table

.. _41: https://github.com/USDA-ARS-NWRC/basin_setup/issues/41
.. _42: https://github.com/USDA-ARS-NWRC/basin_setup/issues/42
.. _43: https://github.com/USDA-ARS-NWRC/basin_setup/issues/43
.. _44: https://github.com/USDA-ARS-NWRC/basin_setup/issues/44
.. _45: https://github.com/USDA-ARS-NWRC/basin_setup/issues/45


0.15.0 (TBD)
-------------------
* Fixes for 46_, 47_
* Added in linting with isort and autopep8
.. _46: https://github.com/USDA-ARS-NWRC/basin_setup/issues/46
.. _47: https://github.com/USDA-ARS-NWRC/basin_setup/issues/47
