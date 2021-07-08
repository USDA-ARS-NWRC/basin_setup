Basin setup update

Group basin setup files into a folder
basin_setup/basin_setup

- main.py
- CoreConfig.ini, each cli would get it's own section down the road
  - seems to be some outdated options, like extents and asym_pad
- convert to logging module
- Perhaps a topo class that creates the topo and interacts with it
- veg folder with latest landfire in it, have the ability to add more similar to WFR, move the csv to there
  - Should we just output the files that are needed to download and let the user download? Leaning this way
- remove point model stuff
- cli.py to create 

There appears to be some gis functionality that could 
basin_setup/gdal

- parse_extents
- check shapefile
- Perhaps do something similar to katana where there is one subprocess function

convert to setuptools_scm if time