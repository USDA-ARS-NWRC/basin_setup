import os

import logging

from basin_setup.utils.logger import BasinSetupLogger
from basin_setup.utils import config
from basin_setup import __version__


class GenerateTopo():

    def __init__(self, config_file):

        self.ucfg, self.configFile = config.read(config_file)
        self.config = self.ucfg.cfg['generate_topo']

        self.basin_setup_logger = BasinSetupLogger(self.ucfg.cfg['logging'])
        self._logger = logging.getLogger(__name__)

        self._logger.info("Generate Topo Tool -- v{0}".format(__version__))

        config.check(self.ucfg, self._logger)

        self.temp_dir = os.path.join(self.config['output_folder'], 'temp')

    def setup_and_check(self):
        """
        Check the arguments that were provided and provide some of the
        directory structure for the setup.
        """

        # Filename and paths and potential sources
        images = {
            'dem': {
                'path': None,
                'source': None
            },
            'basin outline': {
                'path': None,
                'source': None,
                'epsg': None
            },
            'mask': {
                'path': None,
                'source': None,
                'short_name': 'mask'
            },
            'vegetation type': {
                'path': None,
                'source': None,
                'map': None,
                'short_name': 'veg_type'
            },
            'vegetation height': {
                'path': None,
                'source': None,
                'map': None,
                'short_name': 'veg_height'
            },
            'vegetation k': {
                'path': None,
                'source': None,
                'short_name': 'veg_k'
            },
            'vegetation tau': {
                'path': None,
                'source': None,
                'short_name': 'veg_tau'
            },
            'maxus': {
                'path': None,
                'source': None
            }
        }

        # Populate Images for non downloaded files\
        images['dem']['path'] = abspath(expanduser(dem))

        # Add in the subbasins
        if subbasins is not None:
            if not isinstance(subbasins, list):
                subbasins = [subbasins]

            for zz, sb in enumerate(subbasins):
                base = basename(sb).split('.')[0].lower()
                name = base.replace('_outline', '')
                name = name.replace('_subbasin', '')
                name = name.replace('  ', '')  # remove any double spaces
                name = name.replace('_', ' ')
                pth = abspath(expanduser(sb))
                # Capitalize the first letter
                name = proper_name(name)
                # Shapefiles
                images['{} subbasin'.format(name)] = \
                    {'path': pth, 'source': None, 'epsg': None}
                # Images of masks
                images['{} mask'.format(name)] = \
                    {'path': None, 'source': None, 'short_name': '{}'
                     ''.format(name + ' mask')}

        # Populate images for downloaded sources
        images['vegetation type']['source'] = \
            'https://landfire.cr.usgs.gov/bulk/downloadfile.php?FNAME=US_140_mosaic-US_140EVT_20180618.zip&TYPE=landfire'  # noqa

        images['vegetation height']['source'] = \
            'https://landfire.cr.usgs.gov/bulk/downloadfile.php?FNAME=US_140_mosaic-US_140EVH_20180618.zip&TYPE=landfire'  # noqa

        images['vegetation type']['path'] = \
            join(required_dirs['downloads'],
                 'US_140EVT_20180618',
                 'Grid', 'us_140evt',
                 'hdr.adf')

        images['vegetation height']['path'] = \
            join(required_dirs['downloads'],
                 'US_140EVH_20180618',
                 'Grid',
                 'us_140evh',
                 'hdr.adf')

        # Make directories and create setup
        for k, d in required_dirs.items():
            full = abspath(expanduser(d))

            if not isdir(dirname(full)):
                raise IOError("Path to vegetation data/download directory does"
                              " not exist.\n %s" % full)

            if k != 'downloads':
                if isdir(full):
                    out.warn("{0} folder exists, potential to overwrite"
                             " non-downloaded files!".format(k))

                else:
                    out.msg("Making folder...")
                    os.mkdir(full)
            else:
                if isdir(full):
                    out.respond("{0} folder found!".format(k))
                else:
                    out.msg("Making {0} folder...".format(k))
                    os.mkdir(full)

        return images

    def run(self):
        pass
        # Check and setup for an output dir, downloads dir, and temp dir
        # required_dirs = {
        #     'output': self.config['output'],
        #     'downloads': self.config['vegetation_folder']
        # }

        # self.setup_and_check(
        # required_dirs,
        # args.basin_shapefile,
        # args.dem,
        # subbasins=args.subbasins
        # )

        # if args.desired_extents is not None:
        #     out.warn("Using --extents will override any padding requested!")
        #     pad = None
        # else:
        #     # DEM Cell padding
        #     pad = int(args.pad)

        #     # No asymetric padding provided
        #     if args.apad is None:
        #         pad = [pad for i in range(4)]
        #     else:
        #         pad = [int(i) for i in args.apad]

        # # --------- OPTIONAL POINT MODEL SETUP ---------- #
        # if args.point is not None:
        #     out.msg("Point model setup requested!")
        #     images = setup_point(images, args.point, args.cell_size, TEMP, pad,
        #                          args.epsg)
        #     # For point setup the only padding should be around the center pixel
        #     pad = 0
        # else:
        #     images['basin outline']['path'] = \
        #         abspath(expanduser(args.basin_shapefile))

        # images = check_shp_file(images, epsg=args.epsg, temp=TEMP)

        # # ===========================================================================
        # # Downloads and Checking
        # # ===========================================================================
        # images = check_and_download(images, required_dirs)

        # # ===========================================================================
        # # Processing
        # # ===========================================================================
        # images, extents = process(images, TEMP, args.cell_size, pad=pad,
        #                           extents=args.desired_extents)

        # # ===========================================================================
        # # Post Processing
        # # ===========================================================================
        # if args.basin_name is not None:
        #     basin_name = " ".join(args.basin_name)
        # else:
        #     basin_name = None

        # topo = create_netcdf(images, extents, args.cell_size,
        #                      required_dirs['output'], basin_name)
        # # Calculates TAU and K
        # if args.veg_params is None:
        #     veg_params = __veg_parameters__
        # else:
        #     veg_params = args.veg_params
        # topo = calculate_height_tau_k(topo, images, veg_params=veg_params,
        #                               bypass_veg_check=args.bypass_veg_check)

        # # Add the projection information
        # topo = add_proj(
        #     topo,
        #     images['basin outline']['epsg'],
        #     images['dem']['path'])

        # # Making a point
        # if args.point is not None:
        #     if args.uniform:
        #         out.warn("Using uniform flag, all outputted values will the be"
        #                  " equal to the center pixel")

        #         topo = make_uniform(topo, approach='middle')

        #     if args.hill:
        #         topo = make_hill(topo, dem_var='dem')

        # # Don't Flip the image over the x axis if it is not requested
        # if not args.noflip:
        #     out.msg("Flipping images...")
        #     topo = flip_image(topo)

        # topo.close()

        # out.msg('\nRequested output written to:')
        # out.respond('{0}'.format(join(required_dirs['output'], 'topo.nc')))
        # out.msg("Basin setup files complete!\n")

        # # Don't Clean up if we are debugging so we can look at the steps
        # if not DEBUG:
        #     out.msg('Cleaning up temporary files.')
        #     rmtree(required_dirs['temp'])
