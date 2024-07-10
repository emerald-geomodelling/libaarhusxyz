# libaarhusxyz

Parser for the XYZ family of formats for electromagnetic geophysical
measuerement data and resistivity models.

## Supported data formats

* Aarhus Workbench XYZ model format as documented in the [Workbench
reference](http://www.hgg.geo.au.dk/HGGSoftware/workbench/Workbench_A-Z_reference.pdf)
* Aarhus Workbench XYZ data format
* SkyTEM XYZ format

## Supplementary data formats
- Geometry files (.gex), defining the SkyTEM system and the used waveform
- System response files (.sr2)
- Workbench column mappings (.alc)

## Export formats
- geojson of flightlines
- vtk 3d views of resistivity models

## Binary exchange format
This library can also convert to and from a msgpack based container format. This format
can e.g. be read in a web browser, and also removes the issue with numerical precision inherent
in text format to/from float conversion. There's a [javascript companion library](https://github.com/emerald-geomodelling/libaarhusxyz-js)
for working with this format in the browser.

## Examples
For usage details, see [Example usage notebook](docs/Example%20usage.ipynb).

## Other tools
We have developed interface code for the [SimPEG](https://simpeg.xyz/) inversion software to work directly with measured data from SkyTEM systems
(Tested with 304 and 306) in XYZ format using libaarhusxyz. Example notebooks can be found
[here](https://github.com/emerald-geomodelling/experimental-simpeg-ext/).
