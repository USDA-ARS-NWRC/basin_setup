#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('docs/history.rst') as history_file:
    history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read()

setup(
    author="USDA ARS NWRC",
    author_email='snow@ars.usda.gov',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="A python package for building files for hydrologic modeling, specifcally targeting smrf/awsm",
    install_requires=requirements,
    license="CCO 1.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    long_description_content_type='text/markdown',
    package_data={
        'basin_setup': [
            './CoreConfig.ini',
            './recipies.ini'
            './generate_topo/vegetation/landfire_veg_param.csv',
            'qgis_templates/hillshade.xml',
            'qgis_templates/veg_type_colormap.xml',
            'qgis_templates/netcdf_template.xml',
            'qgis_templates/points_template.xml',
            'qgis_templates/raster_template.xml',
            'qgis_templates/stream_template.xml',
            'qgis_templates/shapefile_template.xml',
            'qgis_templates/template.xml',
        ]
    },
    keywords=['basin_setup', 'delineation', 'topo', 'qgis'],
    name='basin_setup',
    packages=find_packages(include=['basin_setup', 'basin_setup.*']),
    entry_points={
        'console_scripts': [
            'generate_topo=basin_setup.cli.generate_topo:main',
            'delineate=basin_setup.delineate:main',
            'grm=basin_setup.grm:main',
            'pconvert=basin_setup.pconvert:main',
            'make_dem_colormap=basin_setup.make_dem_colormap:main',
            'make_veg_type_colormap=basin_setup.make_veg_type_colormap:main',
            'make_qgis_proj=basin_setup.make_qgis_proj:main',
            'nc2shp=basin_setup.convert:nc_masks_to_shp_cli'
        ]},
    test_suite='tests',
    url='https://github.com/USDA-ARS-NWRC/basin_setup',
    version='0.14.6',
    zip_safe=False,
)
