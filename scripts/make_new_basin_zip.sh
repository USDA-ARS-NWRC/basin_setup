#!/bin/bash
################################################################################
# Zips up the new_basin folder to be used other places
# Usage:
#      sh scripts/make_new_basin_zip.sh
#
# Result:
#      Produces a new_basin.zip at the root level of the repo
################################################################################
cd new_basin && \
zip ../new_basin.zip Makefile \
                  pour_points.bna \
                  dem_sources.txt \
                  docker-compose.yml \
