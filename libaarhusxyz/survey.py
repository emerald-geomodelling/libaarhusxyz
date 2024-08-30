from . import xyz as xyzmod
from . import gex as gexmod
import codecs
try:
    import yaml
except:
    pass

class Survey(object):
    def __init__(self, xyz, gex, orig_xyz=None, *arg, **kw):
        if not isinstance(xyz, xyzmod.XYZ): xyz = xyzmod.XYZ(xyz, **kw)
        if not isinstance(gex, gexmod.GEX): gex = gexmod.GEX(gex)
        self.xyz = xyz
        self.orig_xyz = orig_xyz
        self.gex = gex

    def dump(self, xyzfile=None, gexfile=None, alcfile=None, msgpackfile=None, diffmsgpackfile=None, summaryfile=None, geojsonfile=None, simplify=10):
        # FIXME: fill in documentation here 
        # if 'simplify' is none all points make the line in geojson, otherwise it's a tolerance in meters
        if xyzfile: self.xyz.dump(xyzfile, alcfile=alcfile)
        if gexfile: self.gex.dump(gexfile)
        if msgpackfile:
            self.xyz.to_msgpack(
                msgpackfile,
                gex = self.gex)
        if diffmsgpackfile and self.orig_xyz is not None:
            self.orig_xyz.diff(self.xyz).to_msgpack(diffmsgpackfile)
        if summaryfile:
            if hasattr(summaryfile, "write"):
                yaml.dump(self.xyz.summary_dict, codecs.getwriter("utf-8")(summaryfile))
            else:
                with open(summaryfile, "wb") as f:
                    yaml.dump(self.xyz.summary_dict, codecs.getwriter("utf-8")(f))
        if geojsonfile:
            self.xyz.to_geojson(geojsonfile, simplify=simplify)
