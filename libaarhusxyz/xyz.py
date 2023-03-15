import pandas as pd
import numpy as np
try:
    import projnames
except:
    projnames = None

from .xyzparser import dump as _dump_function
from .xyzparser import parse

class XYZ(object):
    """Usage:

    xyz = XYZ(source, **kw)

    Where source can be a filename to parse, or an already parsed
    model dictionary (in the same format returned by xyz.to_dict()).

    Where kw can be:

    alcfile=filename
      Read column mappings from filename (a .ALC file)
    normalize=bool (default False)
      Normalize data after reading.

    Any additional arguments are sent to
    libaarhusxyz.normalizer.normalize()

    """
    def __new__(cls, *arg, **kw):

        normalize = kw.pop("normalize", False)
        alcfile = kw.pop("alcfile", None)
        self = object.__new__(cls)
        if arg:
            if isinstance(arg[0], dict):
                self.model_dict = arg[0]
            else:
                self.model_dict = parse(arg[0], alcfile=alcfile)
        else:
            self.model_dict = {"flightlines": pd.DataFrame(columns=["line_no", "x", "y"]),
                               "model_info": {},
                               "layer_data": {}}
        if normalize:
            self.normalize(**kw)
        return self

    def normalize(self, **kw):
        """This function
             * Normalizes naming and format to our internal format
               (or one specified by naming_standard)
             * Reprojects coordinates
               To lat/lon, web mercator and optionally to a project_crs
             * Calculates xdist
             * Calculate z coordinates
             * Add missing default columns (filled with NaNs)
        """
        from . import normalizer
        normalizer.normalize(self, **kw)

    def normalize_naming(self, naming_standard="libaarhusxyz"):
        from . import normalizer
        normalizer.normalize_naming(self, naming_standard)
    def normalize_projection(self):
        from . import normalizer
        normalizer.normalize_projection(self)
    def normalize_coordinates(self, project_crs=None):
        from . import normalizer
        normalizer.normalize_coordinates(self, project_crs)
    def normalize_dates(self):
        from . import normalizer
        normalizer.normalize_dates(self)
    def normalize_depths(self):
        from . import normalizer
        normalizer.normalize_depths(self)
        
    def add_defaults(self, required_columns=None):
        from . import normalizer
        normalizer.add_defaults(self, required_columns)

    def calculate_xdist(self):
        from . import normalizer
        normalizer.calculate_xdist(self)
    def calculate_z(self):
        from . import normalizer
        normalizer.calculate_z(self)
    def calculate_height(self):
        from . import normalizer
        normalizer.calculate_height(self)
    def calculate_doi_layer(self):
        from . import normalizer
        normalizer.calculate_doi_layer(self)
        
    def dump(self, *arg, **kw):
        _dump_function(self.model_dict, *arg, **kw)

    @property
    def title(self):
        return self.model_info.get("title", self.model_info.get("source", "Unknown"))
        
    @property
    def model_info(self):
        return self.model_dict["model_info"]
    @model_info.setter
    def model_info(self, value):
        self.model_dict["model_info"] = value
        
    @property
    def file_meta(self):
        return self.model_dict["file_meta"]
    @file_meta.setter
    def file_meta(self, value):
        self.model_dict["file_meta"] = value
        
    @property
    def flightlines(self):
        return self.model_dict["flightlines"]
    @flightlines.setter
    def flightlines(self, value):
        self.model_dict["flightlines"] = value
        
    @property
    def layer_data(self):
        return self.model_dict["layer_data"]
    @layer_data.setter
    def layer_data(self, value):
        self.model_dict["layer_data"] = value
    
    @property
    def layer_params(self):
        layer_dfs = self.model_dict["layer_data"]
        if not len(layer_dfs):
            return pd.DataFrame({"layer": []})
        layer_constants = pd.DataFrame(index=next(iter(layer_dfs.values())).columns)
        for key, layer_df in layer_dfs.items():
            if (layer_df.dtypes == float).all():
                if (layer_df.max() - layer_df.min()).max() == 0.0:
                    layer_constants[key] = layer_df.iloc[0]
        return layer_constants.reset_index().rename(columns={"index": "layer"})

    @property
    def projection(self):
        if 'projection' in self.model_info:
            return self.model_info['projection']
        if projnames is None:
            return None
        if "coordinate system" not in self.model_info:
            return None
        return projnames.search(self.model_info["coordinate system"])

    @projection.setter
    def projection(self, value):
        self.model_info['projection'] = value
        
    def to_dict(self):
        return self.model_dict
        
    def __getattr__(self, name):
        # This outer if is only here to make pickle not have a hickup
        if name not in ("model_dict", "model_info", "layer_data", "layer_params"):
            if name in self.model_info:
                return self.model_info[name]
            if name in self.layer_data:
                return self.layer_data[name]
            if name in self.layer_params:
                return self.layer_params[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name not in ("model_dict", "model_info", "layer_data", "layer_params"):
            if name in self.model_info:
                self.model_info[name] = value
            if name in self.layer_data:
                self.layer_data[name] = value
            if name in self.layer_params:
                self.layer_params[name] = value
        object. __setattr__(self, name, value)
    
    def __getitem__(self, line_id):
        return XYZLine(self, line_id)

    def __iter__(self):
        for line_id in self.flightlines["line_id"].unique():
            yield self[line_id]

    @property
    def line_id_column(self):
        for colname in ("line_id", "line_no"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def x_column(self):
        for colname in ("x", "utmx", "lon", "lng"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def y_column(self):
        for colname in ("y", "utmy", "lat"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def z_column(self):
        for colname in ("elevation", "topo"):
            if colname in self.flightlines.columns:
                return colname

    @property
    def alt_column(self):
        for colname in ("alt", "tx_alt"):
            if colname in self.flightlines.columns:
                return colname

    def plot_line(self, line_no, ax=None, **kw):
        if "xdist" not in self.flightlines.columns:
            self.calculate_xdist()
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()
        if "resistivity" in self.layer_data:
            self._plot_line_resistivity(line_no, ax, **kw)
        elif "dbdt_ch1gt" in self.layer_data:
            self._plot_line_raw(line_no, ax, **kw)
        
    def _plot_line_raw(self, line_no, ax, label="gate %(gate)i @ %(time).2e", **kw):
        filt = self.flightlines[self.line_id_column] == line_no
        flightlines = self.flightlines.loc[filt]
        dbdt = self.dbdt_ch1gt.loc[filt]
        times = self.model_info.get('gate times for channel 1', None)
        for gate in range(dbdt.shape[1]):
            i = {"gate": gate,
                 "time": times[gate] if times else "NaN"}
            ax.plot(flightlines.xdist, -dbdt.values[:,gate], label=label % i, **kw)
        ax.set_yscale("log") 
        ax.set_ylabel("|dBdt| (T/s)")
        ax.set_xlabel("xdist (m)")
            
    def _plot_line_resistivity(self, line_no, ax, cmap="turbo", shading='flat', **kw):
        filt = self.flightlines[self.line_id_column] == line_no
        flightlines = self.flightlines.loc[filt]
        resistivity = self.resistivity.loc[filt]
        dep_top = self.layer_data["dep_top"].loc[filt].copy()
        dep_bot = self.layer_data["dep_bot"].loc[filt].copy()

        z = self.z_column
        if z:
            for col in dep_top.columns:
                dep_top[col] = self.flightlines.loc[filt, z] - dep_top[col]
                dep_bot[col] = self.flightlines.loc[filt, z] - dep_bot[col]
        else:
            dep_top = -dep_top
            dep_bot = -dep_bot
                
        xcoords = np.concatenate((flightlines.xdist, flightlines.xdist[-1:]+1))
        zcoords = np.concatenate((dep_top.values, dep_bot.values[:,-1:]), axis=1)
        zcoords = np.concatenate((zcoords, zcoords[-1:,:]))

        data = np.log10(resistivity.values)
        zcoords = zcoords[:,::-1].T
        data = data[:,::-1].T

        ax.pcolor(xcoords, zcoords, data, cmap=cmap, shading=shading, **kw)
        
    def plot(self, fig = None):
        if fig is None:
            import matplotlib.pyplot as plt
            fig = plt.figure()
        
        if "xdist" not in self.flightlines.columns:
            self.calculate_xdist()

        lines = self.flightlines[self.line_id_column].unique()
        w = int(np.ceil(np.sqrt(len(lines))))
        h = int(np.ceil(len(lines) / w))

        axs = fig.subplots(h, w)
        if len(lines) > 1:
            axs = axs.flatten()
        else:
            axs = [axs]
        for line_no, ax in zip(lines, axs):
            self.plot_line(line_no, ax)

    def calculate_xdist(self):
        dxdist = np.insert((  (self.flightlines[self.x_column].iloc[1:].values - self.flightlines[self.x_column].iloc[:-1].values)**2
                            + (self.flightlines[self.y_column].iloc[1:].values - self.flightlines[self.y_column].iloc[:-1].values)**2)**0.5, 0,0)
        self.flightlines["xdist"] = np.cumsum(dxdist)
            
    def __repr__(self):
        max_depth = None
        if "dep_bot" in self.layer_data:
            depths = self.layer_data["dep_bot"].melt()["value"]
            max_depth = depths.loc[~np.isinf(depths)].max()

        resistivity = ""
        if "resistivity" in self.layer_data:
            resistivity = repr(pd.DataFrame(self.resistivity.melt().rename(columns={"value": "Resistivity"})["Resistivity"].describe()))
            
        return "\n".join([
            self.title,
            "--------------------------------",
            repr(pd.DataFrame([self.model_info]).T),
            "",
            "Soundings: %s" % (len(self.flightlines),),
            "Flightlines: %s" % (len(self.flightlines[self.line_id_column].unique()),) if self.line_id_column in self.flightlines.columns else "No line_id column to distinguish lines.",
            "Maximum layer depth: %s" % (max_depth,),
            "Projection: %s" % self.projection,
            repr(self.flightlines[[self.x_column, self.y_column]].describe().loc[["min", "max"]]) if len(self.flightlines) else "",
            resistivity,
            "",
            "Layer data: %s" % (", ".join(set(self.layer_data.keys()) - set(self.layer_params.keys())),),
            "Layer params: %s" % (", ".join(self.layer_params.keys(),)),
            ])
            
            
class XYZLine(object):
    def __init__(self, model, line_id):
        self.model = model
        self.line_id = line_id
    
    @property
    def xdist(self):
        return self.model.flightlines[self.model.flightlines["line_id"] == self.line_id]["xdist"].max()
