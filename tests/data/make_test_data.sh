# PERFORM IN THE DOCKER!

# # Download our data from snow, resize it to 100m for testing only
# scp $SNOW:/data/snowpack/lidar/Lakes/2019/aso/USCALB20190501_SUPERsnow_depth.tif .
# gdalwarp -r bilinear -tr 100 100 USCALB20190325_SUPERsnow_depth.tif USCALB20190325_test_100m.tif
#
# scp $SNOW:/data/snowpack/lidar/Lakes/2019/aso/USCALB20190325_SUPERsnow_depth.tif .
# gdalwarp -r bilinear -tr 100 100 USCALB20190501_SUPERsnow_depth.tif USCALB20190501_test_100m.tif
#
# # Clean up
# rm USCALB20190325_SUPERsnow_depth.tif USCALB20190325_SUPERsnow_depth.tif

delineate -p pour_points.bna -d dem_epsg_32611_100m.tif -o gold -t 1000
rm gold/*.tif gold/lakes_subbasin.* gold/watersheds_* gold/veg_map.csv gold/README.txt

basin_setup --cell_size 150 -dm dem_epsg_32611_100m.tif -bn lakes -f gold/basin_outline.shp -o gold
rm gold/veg_map.csv gold/lidar_depths_wy2019.nc

grm -i USCALB*_test_100m.tif -t gold/topo.nc -b lakes -o gold
