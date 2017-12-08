install:
	cp basin_setup /usr/local/bin/
	chmod +x /usr/local/bin/basin_setup
	

uninstall:
	rm /usr/local/bin/basin_setup

develop:
	chmod +x basin_setup
	ln basin_setup /usr/local/bin/basin_setup
	
