install:
	# Install the python script to the bin
	cp basin_setup /usr/local/bin/
	cp delineate.py /usr/local/bin/delineate
	chmod +x /usr/local/bin/basin_setup
	chmod +x /usr/local/bin/delineate

uninstall:
	# Remove the python script from the bin
	rm /usr/local/bin/basin_setup
	rm /usr/local/bin/delineate

develop:
	# Link the python script so edits are reflected in realtime
	chmod +x basin_setup
	ln basin_setup /usr/local/bin/basin_setup
	chmod +x delineate.py
	ln delineate.py /usr/local/bin/delineate

docker:
	# Build a test docker to play with
	docker build -t test .

test:
	# Test the test docker to ensure things are running
	docker run -it --rm \
								-v $(pwd):/data \
								-v $HOME/Downloads:/data/downloads \
								test \
								-f /data/examples/reynolds_mountain_east/rme_basin_outline.shp \
								-dm /data/examples/reynolds_mountain_east/ASTGTM2_N43W117_dem.tif \
								-d /data/downloads
								--debug
