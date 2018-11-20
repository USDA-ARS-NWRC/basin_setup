#!/usr/bin/env python3

import utm
import argparse
import sys
import pandas as pd
import os
import numpy as np

p = argparse.ArgumentParser(description='Converts points from lat long to utm'
                                        ' and vice versa')

p.add_argument("-c","--coords", dest='coordinates',nargs=2, help= "Provide either lat long or utm coordinates")
p.add_argument("-t","--type", dest="type", default='latlong', help='Specify whether'
               'you are using latlong or utm coordinates, default is latlong')
p.add_argument("-z","--zone", dest="zone", default='latlong', help='Specify whether'
               'you are using latlong or utm coordinates, default is latlong')
p.add_argument("-l","--letter", dest="letter", default='N', help='Specify whether'
               'you are using north or south for UTM default=N')
p.add_argument("-f","--file", dest="file", help='Specify a file containing '
               ' coordinates')

args = p.parse_args()

# Handle a file of points
if args.file != None:
    if not os.path.isfile(args.file):
        print("Error: File does not exist!")
        sys.exit()

    df = pd.read_csv(args.file)

    possible_names = {'latlong':[['lat','lon'],['lat','long'],['latitude','longitude']],
                      'utm':[['x','y'],['northing','easting']]}

    for k,nms in possible_names.items():
        matches = []
        for col in df.columns:
            for n in nms:
                if col.lower() in n:
                    matches.append(col)

        matches = list(set(matches))
        if len(matches) == 2:
            coord_type = k
            break

    if len(matches) != 2:
        print("Error: No lat/longs or x/y's were found in the file. Available columns:\n{})".format(df.columns))
        sys.exit()

    if  coord_type == 'utm':
        print('File contains x,y columns... assuming UTM coords provided!')

        # Add appropriate columns
        print("Adding lat long columns for converted values")
        df['lat'] = pd.Series(np.zeros(len(df.index)), index=df.index)
        df['long'] = pd.Series(np.zeros(len(df.index)), index=df.index)

    # Lat long check
    elif  coord_type == 'latlong':
        print('File contains lat,long columns... assuming lat/long coords provided!')

        # Add appropriate columns
        print("Adding lat long columns for converted values")
        df['x'] = pd.Series(np.zeros(len(df.index)), index=df.index)
        df['y'] = pd.Series(np.zeros(len(df.index)), index=df.index)

    coords = df[matches].values

else:
    coord_type = args.type.lower()
    coords = [[float(c) for c in args.coordinates]]
    # Check if its pair of coordinates was provided.
    if len(args.coordinates) != 2:
        print("Error: Please provide coordinates as a pair!")
        sys.exit()

    # Check for correct type being provided
    if coord_type not in  ['utm', 'latlong']:
        print("Error: Please specify coordinates type as either utm or latlong.")
        sys.exit()

# Loop through the data
for i,coord in enumerate(coords):
    if coord_type == 'utm':
        # Check for zone and utm are provided
        if args.zone == None:
            print("Error: Please provide a zone number with your UTM coordinates.")
            sys.exit()

        data = utm.to_latlon(coord[0],coord[1], int(args.zone),args.letter)

        if args.file != None:
            df['lat'].iloc[i] = data[0]
            df['long'].iloc[i] = data[1]

    elif coord_type == 'latlong':
        data = utm.from_latlon(coord[0],coord[1])

        if args.file != None:
            df['x'].iloc[i] = data[0]
            df['y'].iloc[i] = data[1]

    print(data)

if args.file != None:
    fname = 'converted_{}'.format(os.path.basename(args.file))
    print("Outputting new file with converted coordinates to:\n{}".format(fname))
    df = df.drop(columns=matches)
    df.to_csv(fname,index=False)
