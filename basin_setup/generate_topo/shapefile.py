from subprocess import check_output

from spatialnc.utilities import strip_chars


class Shapefile():

    def __init__(self, file_name) -> None:
        self.file_name = file_name

    @property
    def epsg(self):
        basin_shp_info = check_output(
            ['ogrinfo', '-al', self.file_name],
            universal_newlines=True)

        basin_info = basin_shp_info.split('\n')
        epsg_info = [auth for auth in basin_info if "epsg" in auth.lower()]
        return strip_chars(epsg_info[-1].split(',')[-1])
