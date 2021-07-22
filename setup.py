#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

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
        'Programming Language :: Python :: 3.6',
    ],
    description="A python package for building files for hydrologic modeling, specifcally targeting smrf/awsm",
    install_requires=requirements,
    license="CCO 1.0",
    long_description=readme,
    include_package_data=True,
    long_description_content_type="text/markdown",
    package_data={
        'basin_setup': [
            './CoreConfig.ini',
            './recipes.ini'
            './generate_topo/vegetation/landfire_veg_param.csv'
        ]
    },
    keywords=['basin_setup', 'delineation', 'topo'],
    name='basin_setup',
    packages=find_packages(include=['basin_setup', 'basin_setup.*']),
    entry_points={
        'console_scripts': [
            'generate_topo=basin_setup.cli.generate_topo:main',
            'delineate=basin_setup.delineate:main',
            'grm=basin_setup.grm:main',
        ]},
    test_suite='tests',
    url='https://github.com/USDA-ARS-NWRC/basin_setup',
    zip_safe=False,
    use_scm_version={
        'local_scheme': 'node-and-date',
    },
    setup_requires=[
        'setuptools_scm',
    ],
)
