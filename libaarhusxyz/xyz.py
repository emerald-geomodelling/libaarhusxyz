import pandas as pd
import numpy as np
try:
    import projnames
except:
    projnames = None

import mpl_toolkits.axes_grid1.axes_divider
import matplotlib.pyplot as plt
import matplotlib.colors

from .xyzparser import dump as _dump_function
from .xyzparser import parse
from . import normalizer
import copy

def diff_df(a, b):
    difflen = min(len(a), len(b))
    rows = np.zeros(max(len(a), len(b)), dtype=bool)
    rows[difflen:] = True
    cols = set()
    for col in set(a.columns).union(b.columns):
        if col not in a.columns or col not in b.columns:
            rows[:] = True
            cols.add(col)
        else:
            filt = ~((a.iloc[:difflen][col] == b.iloc[:difflen][col]) | (a.iloc[:difflen][col].isna() & b.iloc[:difflen][col].isna()))
            if filt.sum() > 0:
                cols.add(col)
                rows = rows | filt.values
    return rows, cols

def extract_df(df, rows, cols, annotate=False):
    cols = set(cols)
    if len(rows) > len(df):
        raise NotImplementedError("Can not shorten dataframes")
    else:
        df = df.iloc[rows]        
    res = df[list(cols.intersection(df.columns))].assign(
        **{col: np.nan
           for col in cols if col not in df.columns})
    if annotate:
        res.reset_index(names="apply_idx", inplace=True)
    else:
        res.reset_index(drop=True, inplace=True)
    return res

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
            if isinstance(arg[0], XYZ):
                layer_datas = set().union(*[xyz.layer_data.keys() for xyz in arg])
                model_info = {}
                for xyz in reversed(arg):
                    model_info.update(xyz.model_info)
                
                self.model_dict = {
                    "flightlines": pd.concat([xyz.flightlines for xyz in arg]),
                    "layer_data": {
                        key: pd.concat([xyz.layer_data[key] for xyz in arg
                                        if key in xyz.layer_data])
                        for key in layer_datas
                    },
                    "model_info": model_info
                }
            elif isinstance(arg[0], dict):
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
             * Replaces * with NaN:s
             * Reprojects coordinates
               To lat/lon, web mercator and optionally to a project_crs
             * Calculates xdist
             * Calculate z coordinates
             * Add missing default columns (filled with NaNs)
        """
        normalizer.normalize(self, **kw)

    def normalize_naming(self, naming_standard="libaarhusxyz"):
        normalizer.normalize_naming(self, naming_standard)
    def normalize_nans(self, nan_value=None):
        normalizer.normalize_nans(self, nan_value)
    def normalize_projection(self):
        normalizer.normalize_projection(self)
    def normalize_coordinates(self, project_crs=None):
        normalizer.normalize_coordinates(self, project_crs)
    def normalize_dates(self):
        normalizer.normalize_dates(self)
    def normalize_depths(self):
        normalizer.normalize_depths(self)
        
    def add_defaults(self, required_columns=None):
        normalizer.add_defaults(self, required_columns)

    def calculate_xdist(self):
        normalizer.calculate_xdist(self)
    def calculate_z(self):
        normalizer.calculate_z(self)
    def calculate_height(self):
        normalizer.calculate_height(self)
    def calculate_doi_layer(self):
        normalizer.calculate_doi_layer(self)
        
    def dump(self, nameorfile, alcfile=None):
        """Write to XYZ file.

        nameorfile: either a file path as a string, or an open file object
        to write this object to.

        alcfile: optional file path or open file object to write a
        Aarhus Workbench style ALC file with column mappings to.

        """
        _dump_function(self.model_dict, nameorfile, alcfile=alcfile)

    def to_geojson(self, nameorfile, *arg, **kw):
        from .export import geojson
        geojson.dump(self, nameorfile, *arg, **kw)
        
    def to_msgpack(self, nameorfile, *arg, **kw):
        from .export import msgpack
        msgpack.dump(self, nameorfile, *arg, **kw)
        
    def to_vtk(self, nameorfile, *arg, **kw):
        """Write a 3d model to VTK file (only works for resistivity models,
        not data!).

        nameorfile: either a file path as a string, or an open file object
        to write the VTK file to.

        attr_out: attributes (column names in flightlines, keys in
        layer_data) to include in output.
        """

        from .export import vtk
        vtk.dump(self, nameorfile, *arg, **kw)
        
    @property
    def title(self):
        return self.model_info.get("title", self.model_info.get("source", "Unknown"))
        
    @property
    def info(self):
        return self.model_dict["model_info"]
    @info.setter
    def info(self, value):
        self.model_dict["model_info"] = value
        
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
    def data(self):
        return self.model_dict["layer_data"]
    @data.setter
    def data(self, value):
        self.model_dict["layer_data"] = value
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

    def get_column(self, name):
        if "naming_standard" in self.model_info:
            return normalizer.get_name_mapper(
                self.model_info["naming_standard"])(name)
        for col in self.flightlines.columns:
            if normalizer.default_name_mapper(col) == name:
                return col
        return None
        
    def __getattr__(self, name):
        # This outer if is only here to make pickle not have a hickup
        if name not in ("model_dict", "model_info", "layer_data", "layer_params"):
            if name in self.model_info:
                return self.model_info[name]
            if name in self.layer_data:
                return self.layer_data[name]
            if name in self.layer_params:
                return self.layer_params[name]

            if name.endswith("_column"):
                return self.get_column(name.split("_column")[0])
            
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
        for colname in ("title", "line_id", "line_no", "Line"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def x_column(self):
        for colname in ("x", "utmx", "lon", "lng", "UTMX"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def y_column(self):
        for colname in ("y", "utmy", "lat", "UTMY"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def z_column(self):
        for colname in ("elevation", "topo", "Topography"):
            if colname in self.flightlines.columns:
                return colname

    @property
    def alt_column(self):
        for colname in ("alt", "tx_alt", "tx_altitude"):
            if colname in self.flightlines.columns:
                return colname

    def plot_line(self, line_no, ax=None, **kw):
        """Plots a single flightline/cross section using matplotlib. Any extra
        arguments are sent to `ax.plot()`.

        """
        if "xdist" not in self.flightlines.columns:
            self.calculate_xdist()
        if ax is None:
            import matplotlib.pyplot as plt
            ax = plt.gca()
        if "resistivity" in self.layer_data:
            self._plot_line_altitude(line_no, ax, **kw)
            return self._plot_line_resistivity(line_no, ax, **kw)
        elif "dbdt_ch1gt" in self.layer_data:
            return self._plot_line_raw(line_no, ax, **kw)
        
    def _plot_line_raw(self, line_no, ax, channel=1, label="gate %(gate)i[%(channel)i] @ %(time).2e", **kw):
        filt = self.flightlines[self.line_id_column] == line_no
        flightlines = self.flightlines.loc[filt]

        if channel == 1:
            dbdt = self.dbdt_ch1gt.loc[filt]
            times = self.model_info.get('gate times for channel 1', None)
        elif channel == 2:
            dbdt = self.dbdt_ch2gt.loc[filt]
            times = self.model_info.get('gate times for channel 1', None)
            
        for gate in range(dbdt.shape[1]):
            if "%" in label:
                i = {"channel": channel,
                     "gate": gate,
                     "time": times[gate] if times is not None else np.NaN}
                l = label % i
            elif gate == 0:
                l = label
            else:
                l = None
            ax.plot(flightlines.xdist, np.abs(dbdt.values[:,gate]), label=l, **kw)
        ax.set_yscale("log") 
        ax.set_ylabel("Channel %s |dBdt| (T/s)" % (channel,))
        ax.set_xlabel("xdist (m)")
            
        return ax
        
    def _plot_line_altitude(self, line_no, ax, cmap="turbo", shading='flat', **kw):
        if self.alt_column is None or self.z_column is None:
            return
        filt = self.flightlines[self.line_id_column] == line_no
        flightlines = self.flightlines.loc[filt]
        ax.plot(flightlines.xdist, flightlines[self.alt_column] + flightlines[self.z_column], label="Instrument position")
        
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

        data = resistivity.values
        zcoords = zcoords[:,::-1].T
        data = data[:,::-1].T

        m = ax.pcolor(xcoords, zcoords, data, cmap=cmap, norm=matplotlib.colors.LogNorm(), shading=shading, **kw)

        ax_divider = mpl_toolkits.axes_grid1.axes_divider.make_axes_locatable(ax)
        cax = ax_divider.append_axes("right", size="7%", pad="2%")
        fig = plt.gcf()
        cb = fig.colorbar(m, label="Resistivity (Ωm)", cax=cax)

        return ax
        
    def plot(self, fig = None):
        """Plot this object using matplotlib as a figure. To plot individual
        flightlines / cross sections, use `plot_line(line_no)`.
        """
        
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

        layer_data_names = set(self.layer_data.keys()) - set(self.layer_params.keys())
        layer_data = ", ".join(layer_data_names)

        xyztype = ""
        if "apply_idx" in self.flightlines.columns:
            xyztype = " (diff)"
            layer_data = ", ".join("%s (%s)" % (name, len(self.layer_data[name].columns)) for name in self.layer_data.keys())
            
        coords = ""
        if len(self.flightlines) and self.x_column in self.flightlines.columns and self.y_column in self.flightlines.columns:            
            coords = repr(self.flightlines[[self.x_column, self.y_column]].describe().loc[["min", "max"]])
            
        resistivity = ""
        if "resistivity" in self.layer_data:
            resistivity = repr(pd.DataFrame(self.resistivity.melt().rename(columns={"value": "Resistivity"})["Resistivity"].describe()))

        linenos = "No line_id column to distinguish lines."
        if self.line_id_column in self.flightlines.columns:
            linenos = (len(self.flightlines[self.line_id_column].unique()),) 

        return "\n".join([
            (self.title or "[Unnamed model]") + xyztype,
            "--------------------------------",
            repr(pd.DataFrame([self.model_info]).T),
            "",
            "Soundings: %s" % (len(self.flightlines),),
            "Columns: %s" % (len(self.flightlines.columns),),
            "Flightlines: %s" % linenos,
            "Maximum layer depth: %s" % (max_depth,),
            "Projection: %s" % self.projection,
            coords,
            resistivity,
            "",
            "Layer data: %s" % (layer_data, ),
            "Layer params: %s" % (", ".join(self.layer_params.keys(),)),
            ])

    def diff(self, other):
        rows, flightlines_cols = diff_df(self.flightlines, other.flightlines)

        datasets = set(self.layer_data.keys()).union(other.layer_data.keys())

        layer_data = {}
        
        for dataset in datasets:
            if dataset not in self.layer_data:
                rows[:] = True
                layer_data[dataset] = other.layer_data[dataset].columns
            elif dataset not in other.layer_data:
                rows[:] = True
                layer_data[dataset] = self.layer_data[dataset].columns
            else:
                r, c = diff_df(self.layer_data[dataset], other.layer_data[dataset])
                if r.sum() > 0 and len(c) > 0:
                    rows = rows | r
                    layer_data[dataset] = c
                    
        return type(self)({
            "model_info": {"diff_a_source": self.model_info.get("source", ""), "diff_b_source": other.model_info.get("source", "")},
            "flightlines": extract_df(other.flightlines, rows, flightlines_cols, annotate=True),
            "layer_data": {dataset: extract_df(other.layer_data[dataset], rows, cols)
                           for dataset, cols in layer_data.items()}
        })

    def apply_diff(self, diff):
        res = copy.copy(self)

        rows = diff.flightlines.apply_idx.values

        def df_apply(df, diffdf, rows):
            for col in diffdf.columns:
                if col != "apply_idx":
                    dstcol = type(df.columns[0])(col)
                    df.loc[rows, dstcol] = diffdf[col].values
        
        df_apply(res.flightlines, diff.flightlines, rows)
        
        for dataset, datasetdiff in diff.layer_data.items():
            df_apply(res.layer_data[dataset], datasetdiff, rows)

        return res
        
class XYZLine(object):
    def __init__(self, model, line_id):
        self.model = model
        self.line_id = line_id
    
    @property
    def xdist(self):
        return self.model.flightlines[self.model.flightlines["line_id"] == self.line_id]["xdist"].max()
