#!/usr/bin/env python

import setuptools
import os

setuptools.setup(
    name='libaarhusxyz',
    version='0.0.21',
    description='Parser for the Aarhus Workbench XYZ format for geophysical data',
    long_description="""Parser for the Aarhus Workbench XYZ format for geophysical data""",
    long_description_content_type="text/markdown",
    author='Egil Moeller, Craig William Christensen and others ',
    author_email='em@emeraldgeo.no, cch@emeraldgeo.no',
    url='https://github.com/emerald-geomodelling/libaarhusxyz',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'libaarhusxyz': ['*.csv']},
    install_requires=[
        "numpy",
        "pandas",
        "pyproj",
        "matplotlib"
    ],
    extras_require={
        'normalisation': ["pryproj", "projnames"],
        'tests': ['nose2', 'downfile'],
    }
)
