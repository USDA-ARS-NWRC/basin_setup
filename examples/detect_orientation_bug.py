from netCDF4 import Dataset
import matplotlib.pyplot as plt
from numpy import meshgrid
import numpy as np


data = {"RME":'/home/micahjohnson/projects/basin_setup/examples/reynolds_moutain_east/output/topo.nc'}
point = {}

#'~/projects/smrf/test_data/stationData/ta_metadata.csv'
#f = '/home/micahjohnson/projects/basin_setup/examples/reynolds_moutain_east/output/topo.nc'
f = '/home/micahjohnson/projects/basins/rcew/output/topo_flip.nc'
#f = '/home/micahjohnson/projects/smrf/test_data/topo/topo.nc'

ds = Dataset(f)

xv,yv = meshgrid(ds.variables['x'][:],ds.variables['y'][:])
data = ds.variables['dem'][:]
plt.imshow(data)

#plt.pcolor(xv,yv,data)

# plt.plot(519611,4768129,'ro')
# plt.plot(519976,4768323,'r^')
#plt.axes().set_aspect('equal')

plt.show()
