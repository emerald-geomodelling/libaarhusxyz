#!/usr/bin/env python

import setuptools
import os

setuptools.setup(
    name='libxyz',
    version='0.0.7',
    description='Parser for the Aarhus Workbench XYZ format for geophysical data',
    long_description="""Parser for the Aarhus Workbench XYZ format for geophysical data""",
    long_description_content_type="text/markdown",
    author='Egil Moeller, Craig William Christensen and others ',
    author_email='em@emeraldgeo.no, cch@emeraldgeo.no',
    url='https://github.com/emerald-geomodelling/libxyz',
    packages=setuptools.find_packages(),
    install_requires=[
        "numpy",
        "pandas"
    ],
)
