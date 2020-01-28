"""
Script attempts to rebuild qgis projects using hackish templates made in
qgis. The projects are soley focused on highlight delineation and looking
at the static files going in to AWSM/SMRF

For help on usage:
    python make_qgis_proj.py --help

Author: Micah Johnson
Last Date Modified: 01-24-2020
"""

import datetime
import argparse
from os.path import basename, split, join
import pprint
import requests
from basin_setup.basin_setup import parse_extent


def get_xml_spatial_ref(epsg):
    """
    Construct a string representing how QGIS wants the spatial info

    Returns:
        spatial: String containing a XML representation of the projection
    """
    url = "https://spatialreference.org/ref/epsg/{}/proj4/".format(epsg)
    r = requests.get(url)
    proj4 = r.text.strip()
    data = {}

    for value in proj4.split(" "):
        if 'no_def' not in value:
            val_str = value.replace('+','')
            k,v = val_str.split("=")
            data[k] = str(v)

    sp_ref = (
    '\t\t\t<spatialrefsys>\n'
    '\t\t\t\t<proj4>[PROJ4]</proj4>\n'
    '\t\t\t\t<authid>EPSG:[EPSG]</authid>\n'
    '\t\t\t\t<description>[DATUM] / UTM zone [ZONE]N</description>\n'
    '\t\t\t\t<projectionacronym>utm</projectionacronym>\n'
    '\t\t\t\t<ellipsoidacronym>[DATUM_NO_SPACE]</ellipsoidacronym>\n'
    '\t\t\t\t<geographicflag>false</geographicflag>\n'
    '\t\t\t</spatialrefsys>\n')

    replacement = {"PROJ4": proj4,
                   "EPSG":str(epsg),
                   "DATUM":data['ellps'],
                   "DATUM_NO_SPACE":data['ellps'].replace(" ",'').upper(),
                   "ZONE":data['zone']
                   }
    return str_swap(sp_ref, replacement)

def get_extent_str(fname):
    """
    Parse the extent of a file and provide QGIS with the extents in
    xml format
    """
    if fname.split('.')[-1] == 'bna':
        with open(fname) as fp:
            lines = fp.readlines()
            fp.close()
        x = []
        y = []
        for l in lines:
            #Ignore any lines with quotes in it
            if '"' not in l:
                cx,cy = (float(c) for c in l.strip().split(','))
                x.append(cx)
                y.append(cy)
        xmin = min(x)
        xmax = max(x)
        ymin = min(y)
        ymax = max(y)

    else:
        xmin, ymin, xmax, ymax = parse_extent(fname)

    ext =('\t\t\t<xmin>{}</xmin>\n'
          '\t\t\t<ymin>{}</ymin>\n'
          '\t\t\t<xmax>{}</xmax>\n'
          '\t\t\t<ymax>{}</ymax>').format(xmin, ymin, xmax, ymax)
    return ext


def str_swap(str_raw, replace_dict):
    """
    Goes through a str using the replacement dictionary and looks for the
    keys in brackets and replaces them with the values

    Args:
        str_raw: Original string to replace keywords in using the replace_dictionary
        replace_dict: dictionary containing keywords to replace with full strings from the values

    Returns:
        info: string with keywords that are populated with values
    """

    info = str_raw

    for k,v in replace_dict.items():
        search_str = '[{}]'.format(k)

        info = info.replace(search_str,v)

    return info

def get_now_str():
    """
    Retrieves an iso format of the timestamp for now and returns it with all
    formatting removed e.g. 2020-01-10 10:08.26 -> 20200118100826

    To be used an UID for QGIS.

    Returns:
        str_now: String representing the datetime now for use as a UID
    """

    # QGIS appends an identifier to each so construct it here
    str_now = datetime.datetime.now().isoformat()
    str_now = "".join([c for c in str_now if c not in '-:T.'])

    return str_now

class QGISLayerMaker(object):
    def __init__(self, path, epsg, template_dir='./scripts/qgis_templates', **kwargs):
        """
        Adds a layer to a QGIS project in a hacky XML copy and paste way
        This class is meant to be inherited from with modifications to the
        declaration strings
        """
        # Grab a UID for layer
        self.str_now = get_now_str()

        # Template declaration for a layer. Is inserted near the top of project
        self.declaration =(
        '\t\t<layer-tree-layer expanded="0" providerKey="[PROVIDER]" '
        'checked="Qt::[CHECKED]" id="[NAME][ID]" source="[PATH]" name="[NAME]">\n'
        '\t\t\t<customproperties/>\n'
        '\t\t</layer-tree-layer>\n')

        self.legend = (
        '\t\t<legendlayer drawingOrder="-1" open="true" checked="Qt::[CHECKED]" name="[NAME]" showFeatureCount="0">\n'
        '\t\t\t\t<filegroup open="true" hidden="false">\n'
        '\t\t\t\t\t<legendlayerfile isInOverview="0" layerid="[NAME][ID]" visible="[VISIBLE]"/>\n'
        '\t\t\t\t</filegroup>\n'
        '\t\t</legendlayer>\n')

        # Create an order entry which is getting added to the layers order
        self.order = "\t\t\t<item>[NAME][ID]</item>\n"

        # Create the name from the filename or the variable name
        name = basename(path).split('.')[0]

        # Grab file extension
        self.ext = path.split('.')[-1]

        # Make all layers visible allowing for custom visible layers
        visible = '1'
        checked = 'Checked'

        # Add in the ability to name labels
        display_name = ''

        # Assign a provider and layer_template based on the file ext
        if self.ext == 'shp' or self.ext == 'bna':
            self.ftype = 'shapefile'
            provider = 'ogr'

            # line
            if "net_thresh" in path:
                line_type = 'Line'
                template = join(template_dir, 'stream_template.xml')

            elif 'points' in path:
                line_type = 'Point'
                template = join(template_dir, 'points_template.xml')

                # Hide the pour points but still add to the project
                visible = '0'
                checked = 'Unchecked'

            # Polygon
            else:

                line_type = 'Polygon'
                template = join(template_dir, 'shapefile_template.xml')

                # Add a label for the project subbasins
                if 'subbasin' in path:
                    display_name = name.split('subbasin')[0].replace('_', ' ').title()


            self.replacements = {"PATH": path,
                                "NAME": name,
                                "EPSG": str(epsg),
                                "ID": self.str_now,
                                "LINE_TYPE":line_type,
                                "PROVIDER":provider,
                                "DISPLAY_NAME":display_name}
                                
        elif self.ext == 'tif':
            self.ftype = 'geotiff'
            ftype = 'geotiff'
            provider = 'gdal'
            template = join(template_dir, 'raster_template.xml')

            self.replacements = {"PATH": path,
                                "NAME": name,
                                "EPSG": str(epsg),
                                "ID": self.str_now,
                                "PROVIDER":provider}

        # Netcdf
        elif self.ext == 'nc':
            self.ftype = 'netcdf'
            provider = 'gdal'
            template = join(template_dir, 'netcdf_template.xml')

            self.declaration = (
                '\t\t<layer-tree-layer expanded="0" providerKey="gdal" '
                'checked="Qt::[CHECKED]" id="NETCDF__[NAME]__[VARIABLE][ID]" '
                'source="NETCDF:&quot;[PATH]&quot;:[NC_VAR]" name="NETCDF:'
                '&quot;[NAME]&quot;:[VARIABLE]">\n'
                '\t\t\t<customproperties/>\n'
                '\t\t</layer-tree-layer>\n')

            self.replacements = {"PATH": path,
                                "NAME": name,
                                "VARIABLE":kwargs['variable'],
                                "EPSG": str(epsg),
                                "ID": self.str_now,
                                "PROVIDER":provider}
        else:
            raise ValueError("Unrecognized file format {}".format(self.ext))

        # Assign colors/colormaps
        self.replacements['COLOR'] = self.choose_color_scheme()

        # Retrieve extent
        self.replacements['EXTENT'] = get_extent_str(path)

        # Add in visibility
        self.replacements['VISIBLE'] = visible
        self.replacements['CHECKED'] = checked

        # Retrieve the template for a layer
        print("\tUsing layer template {}".format(template))
        with open(template) as fp:
            self.layer_template = "".join(fp.readlines())

            fp.close()

    def choose_color_scheme(self):
        """
        Whether it is a shapefile or raster or netcdf, this function is able
        to manipulate the replacement dictionary to produce the necessary
        color decisions

        Returns:
            color: string to be used to replace the keyword color in the templates
        """

        # String we are searching for kw to decide on colors
        if self.ftype == 'netcdf':
            # Search the variable name for the kewords
            search_str = self.replacements['VARIABLE'].lower()
        else:
            #Search the path
            search_str = self.replacements['PATH'].lower()

        ###### Universally choose colors ############

        # Use simple gray scale for hillshade rasters
        if 'hillshade' in search_str:
            color = './colormaps/hillshade.qml'

        # Use Custom dem colrmap for the elevation rasters
        elif 'dem' in search_str:
            color = './colormaps/dem_colormap.qml'

        # Use Custom dem colrmap for the elevation rasters
        elif 'veg_type' in search_str:
            color = './colormaps/veg_colormap.qml'

        # streams
        elif "net_thresh" in search_str:
            # Dark blue for streams
            color = "0,50,78,0"

        elif 'pour' in search_str:
            color = "0,227,72,255"

        # Basin/subbasin
        elif 'basin' in search_str:
            # Charcoal
            color = "41,41,41,0"

        else:
            color = ''

        # If we have a colormap file use it only if it is a raster
        if color:
            if self.replacements['PROVIDER']=='gdal':
                # parse the colormap and inject it in to the qgis project
                with open(color) as fp:
                    lines = fp.readlines()
                    fp.close()

                    # Find the index in the colormap where pipe is an self.extract between the two of them
                    idx = [i for i,l in enumerate(lines) if 'pipe' in l]
                    lines = lines[idx[0] + 1:idx[1]]
                    color = "\t\t".join(lines)

        return color

    def generate_strs(self):
        """
        Produces the final three sets of strings to go in the project file
        """
        print("\tProcessing strings for a {}".format(self.ftype))
        declaration = str_swap(self.declaration, self.replacements)
        order = str_swap(self.order, self.replacements)
        layer_def = str_swap(self.layer_template, self.replacements)
        legend = str_swap(self.legend, self.replacements)

        return declaration, order, layer_def, legend

def create_layer_strings(files, epsg, variables=[], declarations='', order='', layers='', legends=''):
    """
    Create three strings to insert in to the qgis project

    Args:
        files: List of paths to georeferences tifs or shapefiles, all files should be in the EPSG projection
        epsg: EPSG value for the project (just for search replace, no reprojections occur)
        variables: Switch to netcdf type and loop over variables
        declarations: String for adding on to provided to force the order of a layer if need be
        order: String for adding on to provided to force the order of a layer if need be
        layers: String for adding on to provided to force the order of a layer if need be
        legend: String for extending to force the order of a legend entry
    Returns:
        declarations: String representing layer declarations
        order: String representing order string in the project file
        layers: String representing the layer definitions
        legend: String representing the legend entries
    """
    if type(files) != list:
        files = [files]

    if variables:
        loop_list = variables
        is_nc = True

    else:
        loop_list = files
        is_nc = False

    # Loop over either files or variables
    for vf in loop_list:
        if is_nc:
            print('Adding {} from {}'.format(vf, files[0]))
            qgs = QGISLayerMaker(files[0], epsg, variable=vf)
        else:
            print('Adding {}'.format(vf))
            qgs = QGISLayerMaker(vf, epsg)

        strs = qgs.generate_strs()
        declarations += strs[0]
        order += strs[1]
        layers += strs[2]
        legends += strs[3]

    return declarations, order, layers, legends

def main():

    parser = argparse.ArgumentParser(description='Build a qgis project for '
                                    'setting up a basin')
    parser.add_argument('-t','--geotiff', dest='tifs', nargs='+',
                        help='Paths to the geotifs to add, specifically looking'
                             ' for a hillshade and dem')
    parser.add_argument('-s','--shapefiles', dest='shapefiles', nargs='+',
                        help='Paths to the shapefiles')
    parser.add_argument('-n','--netcdf', dest='netcdf',
                        help='Path to the input topo file for AWSM')
    parser.add_argument('-v','--variables', dest='variables', nargs='+',
                        help='Variable names in the netcdf to add to the'
                             ' project')

    args = parser.parse_args()
    epsg = 32611

    ######## INPUTS ########
    print("\n\nAdding shapefiles to the project...")
    declarations, order, layers, legends = create_layer_strings(args.shapefiles, epsg)

    print("\n\nAdding variables from a netcdf to the project...")
    declarations, order, layers, legends = create_layer_strings(args.netcdf, epsg,
                                                    variables=args.variables,
                                                    declarations=declarations,
                                                    order=order,
                                                    layers=layers,
                                                    legends=legends)

    print("\n\nAdding geotiffs to the project...")
    declarations, order, layers, legend = create_layer_strings(args.tifs, epsg,
                                                        declarations=declarations,
                                                        order=order,
                                                        layers=layers,
                                                        legends=legends)
    # Populate replacement info
    replacements = \
    {
    "DECLARATIONS":declarations,
    "ORDER": order,
    "LAYERS": layers,
    "LEGEND": legend,
    "EXTENT": get_extent_str(args.tifs[0])
    }
    replacements['SPATIAL_REF'] = get_xml_spatial_ref(epsg)
    template_dir = './scripts/qgis_templates'
    # Open the template
    fname = join(template_dir, 'template.xml')

    with open(fname,'r') as fp:
        lines = fp.readlines()
        fp.close()

    info = "".join(lines)

    info = str_swap(info, replacements)

    out = "setup.qgs"

    with open(out,'w+') as fp:
        fp.write(info)
        fp.close()

if __name__ == '__main__':
    main()
