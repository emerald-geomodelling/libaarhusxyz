from . import xyz as xyzmod
from . import gex as gexmod

class Survey(object):
    def __init__(self, xyz, gex, *arg, **kw):
        if not isinstance(xyz, xyzmod.XYZ): xyz = xyzmod.XYZ(xyz, **kw)
        if not isinstance(gex, gexmod.GEX): gex = gexmod.GEX(gex)
        self.xyz = xyz
        self.gex = gex

    def dump(self, xyzfile=None, gexfile=None, alcfile=None, msgpackfile=None, summaryfile=None):
        if xyzfile: self.xyz.dump(xyzfile, alcfile=alcfile)
        if gexfile: self.gex.dump(gexfile)
        if msgpackfile:
            self.xyz.to_msgpack(
                msgpackfile,
                gex = self.gex)
        if summaryfile:
            with open(summaryfile, "w") as f:
                yaml.dump(xyz.summary_dict, f)
                    
