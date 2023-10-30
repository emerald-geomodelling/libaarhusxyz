from . import xyz as xyzmod
from . import gex as gexmod

class Survey(object):
    def __init__(self, xyz, gex, *arg, **kw):
        if not isinstance(xyz, xyzmod.XYZ): xyz = xyzmod.XYZ(xyz, **kw)
        if not isinstance(gex, gexmod.GEX): gex = gexmod.GEX(gex)
        self.xyz = xyz
        self.gex = gex

    def dump(self, xyzfile=None, gexfile=None, alcfile=None):
        if xyzfile: self.xyz.dump(xyzfile, alcfile=alcfile)
        if gexfile: self.gex.dump(gexfile)
