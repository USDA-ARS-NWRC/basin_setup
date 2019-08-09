#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('docs/history.rst') as history_file:
    history = history_file.read()

requirements = [ ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Micah Johnson",
    author_email='micah.johnson150@gmail.com',
    classifiers=[
        'Development Status :: 4 - beta',
        'Intended Audience :: Developers',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description="A python package for building files for hydrologic modeling specifcally targeting smrf/awsm",
    install_requires=requirements,
    license="CCO 1.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    package_data={'basin_setup':['./landfire_veg_param.csv']},
    keywords=['basin_setup','delineation','topo',],
    name='basin_setup',
    packages=find_packages(include=['basin_setup']),
    entry_points={
    'console_scripts': [
        'basin_setup=basin_setup.basin_setup:main',
        'delineate=basin_setup.delineate:main',
        'grm=basin_setup.grm:main',
        'pconvert=basin_setup.pconvert:main'
    ]},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/USDA-ARS-NWRC/basin_setup',
    version='0.11.1',
    zip_safe=False,
)
