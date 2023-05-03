# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


import os
import libaarhusxyz


# %% load the sounding data (xyz)

dirname_xyz="/Path/to/your/file"
filename_xyz_in="my_input_file.XYZ"
fullfilename_xyz_in = os.path.join(dirname_xyz, filename_xyz_in)

data=libaarhusxyz.parse(fullfilename_xyz_in)


# %% write AEM data to file:


filename_xyz_out="my_output_file.xyz"
fullfilename_xyz_out = os.path.join(dirname_xyz, filename_xyz_out)
libaarhusxyz.dump(data, fullfilename_xyz_out)
