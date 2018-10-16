install:
	# Install the python script to the bin
	cp basin_setup /usr/local/bin/
	chmod +x /usr/local/bin/basin_setup

uninstall:
	# Remove the python script from the bin
	rm /usr/local/bin/basin_setup

develop:
	# Link the python script so edits are reflected in realtime
	chmod +x basin_setup
	ln basin_setup /usr/local/bin/basin_setup

dbuild:
	# Build a test docker to play with
	docker build -t test .

test:
	# Test the test docker to ensure things are running
	docker run -it --rm \
								-v $(pwd):/data \
								-v ~/Downloads:/data/downloads \
								test \
								-f /data/examples/reynolds_mountain_east/rme_basin_outline.shp \
								-dm /data/examples/reynolds_mountain_east/ASTGTM2_N43W117_dem.tif \
								-d /data/downloads
								--debug
