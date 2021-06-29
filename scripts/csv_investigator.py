import numpy as np
import pandas as pd
from netCDF4 import Dataset

#name = "veg_type"
name = 'veg_height'

if name == 'veg_type':
    f = '/home/micahjohnson/Downloads/US_140EVT_04252017/CSV_Data/LF_140EVT_09152016.csv'

elif name == 'veg_height':
    f = '/home/micahjohnson/Downloads/US_140EVH_12052016/CSV_Data/LF_140EVH_05092014.csv'


topo_f = '/home/micahjohnson/Documents/rme/output/topo.nc'
topo = Dataset(topo_f,'r')
veg_value = np.unique(np.array(topo.variables[name][:]))
d = pd.read_csv(f)
ind = d['VALUE'].isin(veg_value)
print(d.ix[ind])
print(d['VALUE'].tolist())
#print(d[['VALUE','EVT_CLASS','EVT_PHYS']].ix[d['VALUE'].isin(veg_value)])
topo.close()
