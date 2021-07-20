import argparse

from basin_setup.generate_topo import GenerateTopo


def main():

    # Parge command line arguments
    p = argparse.ArgumentParser(
        description='Setup a new basin for SMRF/AWSM.'
        ' Creates all the required static files'
        ' required for running a basin. The output is a'
        ' topo.nc containing: dem, mask, veg height,'
        ' veg type, veg tau, and veg k')

    p.add_argument(dest='config_file',
                   help="Path to configuration file")

    args = p.parse_args()

    gt = GenerateTopo(args.config_file)
    gt.run()


if __name__ == '__main__':
    main()
