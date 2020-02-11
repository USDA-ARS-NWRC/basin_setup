"""
Script will add veg types to a csv. Its designed to help users walk through
the decision making process fro veg tau and K
"""
from tabulate import tabulate
import pandas as pd
import argparse
from os.path import dirname, basename, join, abspath, expanduser
from collections import OrderedDict
import basin_setup
import sys
import os
import time
import subprocess as sp


def clear_term():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_table(dataframe=False):
    table = OrderedDict({'open':{'tau':1,'k':0},
            'deciduous':{'tau':0.44,'k':0.025},
            'mix conifer/deciduous':{'tau':0.3,'k':0.033},
            'medium conifer':{'tau':0.2,'k':0.04},
            'dense conifer':{'tau':0.16,'k':0.074}})

    if dataframe:
        df = pd.DataFrame(columns=['canopy class','tau','k'])
        for k,v in table.items():
            df = df.append({'canopy class':k, 'tau':table[k]['tau'], 'k':table[k]['k']}, ignore_index=True)
        return df
    return table

def print_links_1999_table(markdown=False):
    """
    Prints out the table from LINKS 1999
    """
    table = get_table()
    msg = "{0:<25}{1:<10}{2:<10}"
    hdr = msg.format("Canopy Class", 'Tau', 'K')
    print("=" * len(hdr))
    print(hdr)
    print("=" * len(hdr))
    msg = "{0:<25}{1:<10.2f}{2:<10.3f}"

    for k,v in table.items():
        print(msg.format(k.title(), v['tau'], v['k']))
    print('\n')

def main():
    """
    Commmand line function taking in args to manipulate the veg type csv in
    basin_setup
    """
    # Parge command line arguments
    p = argparse.ArgumentParser(description='Enables users to walk through a'
                                            ' series of veg types to add veg k'
                                            ' and tau to the landfire veg '
                                            ' params in basin setup.')

    p.add_argument('-v','--veg_types', dest='veg_types',
                required=True, nargs='+',
                help="Veg typ values that are missing from basin setup veg csv")
    p.add_argument('-lf','--landfire', dest='landfire',
                default='~/Downloads/US_140EVT_20180618/CSV_Data/LF_140EVT_09152016.csv',
                help="Path to the landfire data CSV description file")

    args = p.parse_args()

    # Create the dataframe from the original landfire dataset
    dfo = pd.read_csv(abspath(join(expanduser(args.landfire))))
    dfo = dfo.set_index('VALUE')

    # Create a dataframe from the current landfire data types
    dfc = pd.read_csv(basin_setup.__veg_parameters__)
    dfc = dfc.set_index('veg')

    pertinent_cols = ['CLASSNAME',
                      'EVT_Fuel',
                      'EVT_Fuel_N',
                      'EVT_LF',
                      'EVT_GP',
                      'EVT_PHYS',
                      'EVT_GP_N',
                      'SAF_SRM',
                      'EVT_ORDER',
                      'EVT_CLASS',
                      'EVT_SBCLS']

    # Gather valid canopy classes
    table = get_table()
    valid_canopy = list(table.keys())

    veg_types = [int(v) for v in args.veg_types]
    # Go over all the veg values the user passed
    for i,vt in enumerate(veg_types):
        # Clear the screen
        clear_term()
        print('\n{} does not have a tau/K assigned in basin_setup...\n'.format(vt))

        # Check if it is valid.
        if int(vt) not in dfo.index:
            print("{} is not a valid veg type according to Landfire.".format(vt))
            print(type(dfo.index[0]))

        # Check if it already exists
        elif vt in dfc.index:
            print("Veg Type value {} has already been assigned a K/Tau values in basin_setup.")

        else:
            # print the tau K table
            print("Table 1: K/tau values by Canopy Class")
            print_links_1999_table()
            print('\n')

            # Print the Landfire description with a header
            table_2 = "Table 2: LF Descriptions for Vegetation Type = {}".format(vt)
            print(table_2)
            print("=" * len(table_2))
            print(dfo[pertinent_cols].loc[vt])

            # Print the prompt for values
            print("\n\nUsing Tables 1 and 2, estimate the vegetation paramter tau and K for veg type = {}...\n".format(vt))
            valid = False

            while not valid:
                cc = input("Choose a canopy class:\n").strip()
                if cc.lower() not in [c.lower() for c in valid_canopy]:
                    valid = False
                    print("\nInvalid canopy selection, please use one of the following: \n{}\n\n".format("\n".join(valid_canopy)))
                else:
                    valid = True

            # Add the new information to the current dataframe and output it
            data = dfo[[c for c in dfc.columns if c not in ['tau','k']]].loc[vt]
            data['tau'] = table[cc]['tau']
            data['k'] = table[cc]['k']

            print("\nAssigning Tau = {:0.2f} and K = {:0.3f} for veg type = {}".format(data['tau'], data['k'], vt))
            dfc.loc[vt] = data
            dfc.to_csv('out.csv')
            print("Modified {}/{} veg types.".format(i+1,len(veg_types)))
            input("\nPress enter to continue...")

    # Print nice and handy overview message
    print("\n\n\nThe following are the selections made during this session:\n\n")
    print_cols = [c for c in pertinent_cols if c not in ['EVT_Fuel','EVT_GP']] + ['tau','k']
    s = tabulate(dfc[print_cols].loc[veg_types], tablefmt="pipe", headers="keys")
    st = tabulate(get_table(dataframe=True), tablefmt="pipe", headers="keys")

    with open("results.md",'w+') as fp:
        fp.write(st)
        fp.write('\n\n')
        fp.write(s)
        fp.close()

    print(dfc[print_cols].loc[veg_types])
    print('\n\n\n')
    cmd = 'pandoc results.md -V geometry:landscape -V fontsize=7pt -V geometry:margin=0.1in -f markdown -o results.pdf'
    sp.check_output(cmd, shell=True)

if __name__ == '__main__':
    main()
