from subprocess import check_output
import re
import netCDF4 as nc


def parse_extent(fname, x_field='x', y_field='y'):
    """ Parse the information of some GIS file and returns a
    list of the response of the things important to this script.

    shapefile uses ogrinfo
    tif uses gdalinfo
    asc reads the header
    netcdf uses nc.Dataset x_field and y_field

    Args:
        fname: Full path point to file containing GIS information

    Returns:
        extent: containing images extent in list type
            [x_ll, y_ll, x_ur, y_ur]
        cellsize: cell size for the image
    """

    cellsize = None

    # regular expression to look for numbers within parenthisis
    regex = re.compile(r"\((.*?)\)")

    file_type = fname.split('.')[-1]
    if file_type == 'shp':
        basin_shp_info = check_output(['ogrinfo', '-al', fname],
                                      universal_newlines=True)
        parse_list = basin_shp_info.split('\n')

        # Parse extents from basin info
        for line in parse_list:
            if 'extent:' in line.lower():
                extent = [float(xi) for x in regex.findall(line)
                          for xi in x.split(',')]

                break

    elif file_type == 'tif':
        basin_shp_info = check_output(
            ['gdalinfo', fname], universal_newlines=True)
        parse_list = basin_shp_info.split('\n')
        extent = []

        for line in parse_list:
            ll = line.lower()

            if 'pixel size' in ll:
                # 'pixel size = (100.000000000000000,-100.000000000000000)'
                cellsize = float(regex.findall(ll)[0].split(',')[0])

            if 'lower left' in ll or 'upper right' in ll:
                # matching a line that looks like this
                # 'lower left  (  318520.405, 4157537.075) (119d 3\'15.63"w, 37d32\'49.14"n)' # noqa
                match = regex.findall(ll)[0]  # only need the first one
                extent += [float(x) for x in match.split(',')]

    elif file_type == 'asc':

        ascii_file = open(fname, 'r')

        ascii_headlines = []
        ascii_headlines = [ascii_file.readline().strip('\n')
                           for i_line in range(6)]
        ascii_file.close()

        parse_list = ascii_headlines
        extent = []
        n_rows = 0
        n_cols = 0
        x_ll = 0
        y_ll = 0
        cellsize = 0

        for line in parse_list:
            ll = line.lower()
            w = line.split(' ')
            if 'xllcorner' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                x_ll = float(w[-1])
            elif 'yllcorner' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                y_ll = float(w[-1])
            elif 'ncols' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                n_cols = float(w[-1])
            elif 'nrows' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                n_rows = float(w[-1])
            elif 'cellsize' in ll:
                w = [w[i_w] for i_w in range(len(w)) if w[i_w] != '']
                cellsize = float(w[-1])

            extent = [x_ll, y_ll,
                      x_ll + (n_cols) * cellsize,
                      y_ll + (n_rows) * cellsize]

    elif file_type == 'nc':

        ncfile = nc.Dataset(fname, 'r')

        # Extract fields of interest
        x_vector = ncfile.variables[x_field][:]
        y_vector = ncfile.variables[y_field][:]

        # Determine extents of input netCDF file
        n_cols = len(x_vector)
        n_rows = len(y_vector)

        # Be careful if coordinate system is lat-lon and southern
        # hemisphere, etc.
        # Should be in meters (projected coordinate system)
        dx = abs(x_vector[1] - x_vector[0])  # in meters
        dy = abs(y_vector[1] - y_vector[0])  # in meters

        # the nc_file uses center of cell coords
        # Change if not cell center coords
        x_ll = x_vector.min() - dx / 2
        y_ll = y_vector.min() - dy / 2

        extent = [x_ll, y_ll,
                  x_ll + (n_cols) * dx,
                  y_ll + (n_rows) * dy]

        cellsize = [dx, dy]
        ncfile.close()

    else:
        raise IOError("File type .{0} not recoginizeable for parsing extent"
                      "".format(file_type))

    return extent, cellsize
