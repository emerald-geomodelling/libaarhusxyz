#!/usr/bin/env python

import setuptools
import os

setuptools.setup(
    name='libaarhusxyz',
    version='0.0.6',
    description='Parser for the Aarhus Workbench XYZ format for geophysical data',
    long_description="""Parser for the Aarhus Workbench XYZ format for geophysical data""",
    long_description_content_type="text/markdown",
    author='Egil Moeller, Craig William Christensen and others ',
    author_email='em@emeraldgeo.no, cch@emeraldgeo.no',
    url='https://github.com/emerald-geomodelling/libaarhusxyz',
    packages=setuptools.find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
    extras_require={
        'tests': ['nose2', 'downfile'],
    }
)
