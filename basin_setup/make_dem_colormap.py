"""
Generate a dem_style.qml. These are best loaded in to QGIS using the properties
menu under the styles tab

usage:
    python make_dem_colormap.py dem.tif

output:
    a style file written to dem_style.qml

"""

import argparse
from collections import OrderedDict
from subprocess import check_output

import numpy as np


def main():
    # Manage arguments
    parser = argparse.ArgumentParser(description='Create a colormap for a dem')
    parser.add_argument('dem', metavar='d',
                        help='Path to a dem images that can be evaluated by gdal_info')
    args = parser.parse_args()

    print("Creating a new colormap for QGIS based on the veg values found in the topos")
    cmd = "gdal_info -stats {}".format(args.dem)

    output = "./colormaps/dem_colormap.qml"

    print("Parsing dems max and min...")
    cmd = "gdalinfo -stats {}".format(args.dem)
    s = check_output(cmd, shell=True)
    stats = {}

    # Parse the output of gdalinfo
    for line in s.decode('utf-8').split("\n"):
        ll = line.lower()
        if "statistics_" in ll:
            if "=" in ll:
                name, value = ll.split("=")
                name = name.split("_")[-1]
                value = float(value.strip())
                stats[name] = value

    # Double color ramp, 0 transparent, 1-30% Dark green to light brown, to
    # white
    colors = OrderedDict()
    colors[0.01] = [76, 119, 72]
    colors[0.28] = [89, 86, 0]
    colors[0.47] = [119, 75, 0]
    colors[0.7] = [146, 110, 49]
    colors[0.8] = [173, 146, 101]
    colors[0.85] = [255, 255, 255]

    alpha = 200

    print("Creating a new colormap for QGIS based on the DEM found in the topos")

    # Upper portion of the style file right up to the color ramp
    hdr = """
    <!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
    <qgis version="2.18.28" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
      <pipe>
        <rasterrenderer opacity="1" alphaBand="-1" classificationMax="{}" classificationMinMaxOrigin="CumulativeCutFullExtentEstimated" band="1" classificationMin="{}" type="singlebandpseudocolor">
          <rasterTransparency/>
          <rastershader>
            <colorrampshader colorRampType="INTERPOLATED" clip="0">
    """

    # lower portion of the style file right after the color ramp
    footer = """
            </colorrampshader>
          </rastershader>
        </rasterrenderer>
        <brightnesscontrast brightness="0" contrast="0"/>
        <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
        <rasterresampler maxOversampling="2"/>
      </pipe>
      <blendMode>0</blendMode>
    </qgis>
    """

    color_entry = '          <item alpha="{0}" value="{1}" label="{1}" color="{2}"/>\n'

    # Grab the veg values for all the modeling domains in the sierras
    with open(output, 'w+') as fp:

        # Write the upper portion of the file
        fp.write(hdr.format(stats['maximum'], stats['minimum']))

        # Number of colors dictate the number of color separations
        n_colors = len(colors)

        # Always add a 0-1 thats transparent
        hex_v = '#%02x%02x%02x' % (255, 255, 255)
        fp.write(color_entry.format(0, 0, hex_v))

        for percent, rgb in colors.items():

            # Snag the value from the linspace
            value = (stats['maximum'] - stats['minimum']) * \
                percent + stats['minimum']

            # Form the hex value
            hex_v = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])

            # Output the data
            fp.write(color_entry.format(alpha, value, hex_v))

        print("Built a colormap using {} colors to represent the dem.".format(
            len(colors.keys())))

        # Write the rest of the file
        fp.write(footer)
        fp.close()

    print("Complete!")


if __name__ == 'main':
    main()
