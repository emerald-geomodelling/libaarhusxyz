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

    # FIXME: fill in the rest here
    # def __str__(self):
    #     stuff

    # def plot(self):
    #     Stuff

    def dump(self,
             xyzfile: str = None,
             gexfile: str = None,
             alcfile: str = None,
             msgpackfile: str = None,
             diffmsgpackfile: str = None,
             summaryfile: str = None,
             geojsonfile: str = None,
             simplify: int = 5):
        """
        Write survey to file(s)

        Parameters
        ----------
        xyzfile :
            If not None, filepath to write the xyzfile
        gexfile :
            If not None, filepath to write the gexfile
        alcfile :
            If not None, filepath to write the alcfile
        msgpackfile :
            If not None, filepath to write the msgpackfile
        diffmsgpackfile :
            If not None, filepath to write the diffmsgpackfile
        summaryfile :
            If not None, filepath to write the summaryfile
        geojsonfile :
            If not None, filepath to write the geojsonfile
        simplify :
            Only applies to the geojsonfile.
            Simplifies filightlines by removing relatively extraneous vertices while preserving essential shape within {simplify} m.
            If simplify == 0, no simplification will occur
        """
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

    def plot(self):
        self.gex.plot()
        self.xyz.plot()

    def __repr__(self):
        return "%s\n\n%s" % (self.gex, self.xyz)
    
    def _ipython_display_(self):
        self.plot()
        
        
