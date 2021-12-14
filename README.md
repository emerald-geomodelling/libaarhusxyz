# libaarhusxyz

Parser for the Aarhus Workbench XYZ format as documented in the [Workbench reference](http://www.hgg.geo.au.dk/HGGSoftware/workbench/Workbench_A-Z_reference.pdf) for geophysical data.




The library can also read
- Geometry files (.gex), defining the SkyTEM system and the used waveform
- system response files (.sr2)
- usage examples can be found under ./examples  




# Usage

    >>> import libaarhusxyz
    >>> data = libaarhusxyz.parse("file.xyz")
    >>> data["model_info"]
    {'info': 'Aarhus Workbench export file. File created: 01-01-2021 12:01:01. Exported from /Workbench64 . User: J. Random',
     'wb version': '6.0.1.0',
     'node name(s)': 'SCI_1',
     'dummy': 9999.0,
     'data unit': 'dB/dt [V/Am^4]',
     'data type': 'DTSKYTEM2',
     'coordinate system': 'WGS 84 UTM zone 32N (epsg:32632)',
     'number of layers': 25.0,
     'model unit': 'Resistivity (Ohm-m) / conductivity (mS/m)',
     'number of gates': 40.0,
     'gate times': [8.35e-06, 1.034e-05, 1.285e-05, ... 0.002292, 0.002848, 0.003534]}
    >>> data["flightlines"]
       line_no      utmx       utmy     timestamp  ...  resdata  restotal  doi_conservative  doi_standard
    0        0  123437.3  1234301.0  43318.550666  ...    3.826     1.192           140.106       250.011
    1        0  123451.4  1234328.0  43318.550683  ...    2.814     1.192           110.112       140.106
    2        0  123461.9  1234380.5  43318.550700  ...    1.543     1.192            87.564       102.617
    3        0  123472.6  1234371.0  43318.550718  ...    1.286     1.192            50.545       109.178
    4        0  123482.0  1234402.5  43318.550735  ...    2.251     1.192            60.881       118.525
    >>> data["layer_data"].keys()
    dict_keys(['rho_i', 'rho_i_std', 'sigma_i', 'dep_top', 'dep_bot', 'thk', 'thk_std', 'dep_bot_std'])
    >>> data["layer_data"]["rho_i"]
               0           1           2           3   ...          21          22          23          24
    0  242.803478  422.687883  357.301035  789.825836  ...  121.079258   24.580480  427.934271  655.141307
    1  719.697620   82.651076  834.310254  287.236415  ...  133.897025  143.792923  934.603029  160.595448
    2   16.286573   86.279049  158.523177  237.963008  ...  328.158339  571.532269  590.897296  372.639707
    3  196.942396  576.447067   64.198719  159.602651  ...  895.423804  688.420991  242.795464  109.360430
    4  323.119234  470.146320  139.959078  105.866275  ...  953.291013  486.466359  740.259246  532.806194

    # Upsample soundings to all have the same layer boundaries
    >>> data = normalize_layer_depths(data)

    # Save to new file
    >>> libaarhusxyz.dump(data, "newfile.xyz")
    

