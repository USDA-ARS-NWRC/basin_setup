"""
Reads the CSV in the land fire data set and attempts to make a colormap on the
veg description for the csv. Provide the path to the unzip vegetation dir

Usage:
    python make_veg_type_colormap.py ~/Downloads/US_140EVT_20180618
"""

import pandas as pd
import numpy as np
from collections import OrderedDict

def main():

    parser = argparse.ArgumentParser(description='Generate a colormap for the Landfire data')
    parser.add_argument('veg_dir', help='Path to vegetation top level dir')

    args = parser.parse_args()

    fname = join(args.veg_dir, "CSV_Data/LF_140EVT_09152016.csv")

    print("Creating a new colormap for QGIS based on the vegetation type values.")

    output = "./colormaps/veg_colormap.qml"


    print("Parsing vegetation types...")
    df = pd.read_csv(fname)

    stats = {"minimum":df['VALUE'].min(), "maximum": df['VALUE'].max()}
    norm = 100
    cm_types = {'water':        {'alpha':200, 'color':[0, 50, 78], 'tags':['water']},
                'forest':       {'alpha':norm, 'color':[1, 68, 33],'tags':['forest']},
                'sage':         {'alpha':norm,'color':[161, 168, 143],'tags':['sagebrush']},
                'snow':         {'alpha':norm,'color':[255, 231, 228],'tags':['snow']},
                'developed':    {'alpha':norm, 'color':[92, 94, 88],'tags':['developed']},
                #'barren':       {'alpha':norm, 'color':[131, 117, 96],'tags':['barren']},
                # 'grass':        {'alpha':norm, 'color':[228, 242, 210],'tags':['grass']},
                'lush':         {'alpha':norm, 'color':[58, 95, 11],'tags':['meadow','riparian']},
                # 'bush':         {'alpha':norm, 'color':[0, 144, 64], 'tags':['shrub']},
                }
    df = df.set_index('VALUE').sort_index()
    print("Creating a new colormap for QGIS based on the DEM found in the topos")

    # Upper portion of the style file right up to the color ramp
    hdr = """
    <!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
    <qgis version="2.18.28" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
      <pipe>
        <rasterrenderer opacity="1" alphaBand="-1" classificationMax="{}" classificationMinMaxOrigin="CumulativeCutFullExtentEstimated" band="1" classificationMin="{}" type="singlebandpseudocolor">
          <rasterTransparency/>
          <rastershader>
            <colorrampshader colorRampType="EXACT" clip="0">
    """

    # lower portion of the style file right after the color ramp
    footer = """
            </colorrampshader>
          </rastershader>
        </rasterrenderer>
        <brightnesscontrast brightness="0" contrast="0"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </qgis>
    """

    color_entry = '          <item alpha="{0}" value="{1}" label="{2}" color="{3}"/>\n'


    print(df['CLASSNAME'])

    # Grab the veg values for all the modeling domains in the sierras
    with open(output,'w+') as fp:

        # Write the upper portion of the file
        fp.write(hdr.format(stats['maximum'], stats['minimum']))

        # Loop through every veg value
        for veg_value, row in df.iterrows():

            # USe classname to find keywords
            classname = row['CLASSNAME']

            # SPecify defaults
            legend_name = 'N/A'
            alpha = 0
            rgb = [0, 0, 0]

            # Loop through  any assigned options
            for name, details in cm_types.items():

                # If we have any tag matches
                if [True for kw in details['tags'] if kw in classname.lower()]:
                    # Snag the value from the linspace
                    rgb = details['color']
                    alpha = details['alpha']
                    legend_name = name
                    break

            # Form the hex value
            hex_v = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])

            # Output the data
            fp.write(color_entry.format(alpha, veg_value, name, hex_v))

        print("Built a colormap using {} veg types.".format(len(df.index)))

        # Write the rest of the file
        fp.write(footer)
        fp.close()

    print("Complete!")

if __name__ == 'main':
    main()
