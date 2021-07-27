import geopandas as gpd
from rasterio import features


class Shapefile():

    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.polygon = gpd.read_file(self.file_name)

    @property
    def crs(self):
        """The EPSG code for the shapefile  

        Returns:
            str: EPSG code, ex 'epsg:32611'
        """
        return self.polygon.crs.srs

    def mask(self, nx, ny, transform):
        """Create a raster mask from the shapefile using rasterio.features.rasterize

        Args:
            nx (int): number of x cells
            ny (int): number of y cells
            transform (list): Affine transformation

        Returns:
            np.ndarray: 1 for locations inside the mask, 0 for outside
        """

        return features.rasterize(
            self.polygon.geometry,
            out_shape=(ny, nx),
            fill=0,
            transform=transform
        )
