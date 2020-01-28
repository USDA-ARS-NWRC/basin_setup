"""
This file merges the  veg k and tau csv with the original veg_parameters file
from landfire.

The result is an informative file used for basin_setup delivering veg tau and k
"""

import pandas as pd

# Original landfire dataset
landfire_csv = "~/Downloads/US_140EVT_20180618/CSV_Data/LF_140EVT_09152016.csv"

# Existing basin_setup veg_parameters file, missing all the veg info except tau and K and value
veg_tau_k_csv = "./veg_tau_k.csv"

# Edited values to tau and k on a few parameter
edited_landfire_csv = "~/Downloads/landfire_veg_param.csv"


# Open and declutter ther original dataset
original = pd.read_csv(landfire_csv)

# Grab only relevant columns and set the index to the vegetation value
relevant = [ 'CLASSNAME', 'EVT_Fuel', 'EVT_Fuel_N', 'EVT_LF', 'EVT_GP',
       'EVT_PHYS', 'EVT_GP_N', 'SAF_SRM', 'EVT_ORDER', 'EVT_CLASS',
       'EVT_SBCLS','VALUE']
original = original[relevant].set_index("VALUE")

# Open the edited landfire dataset fin which values have tau and K
edited_landfire = pd.read_csv(edited_landfire_csv)
edited_landfire = edited_landfire.set_index("VALUE")

# Open the basin setup file and set its index to the veg column.
tau_k = pd.read_csv(veg_tau_k_csv)
tau_k = tau_k.set_index('veg')

# Grab all the veg descriptor columns and add it back to the basin_setup version
ind = original.index.isin(tau_k.index)
tau_k[original.columns] = original[ind]

# Find all the veg values that were added in which should only be a couple
ind = edited_landfire.index.isin(tau_k.index)
changed = edited_landfire[ind]

a = tau_k.loc[changed.index]

ind = a['tau'] != changed['tau']

print("Tau and K was:")
print(a[['tau','k']][ind])
print("Changed to :")
print(changed[['tau','k']][ind])

tau_k.loc[changed[ind].index] = changed

tau_k.to_csv("test.csv")
