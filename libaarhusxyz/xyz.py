# Originally from https://github.com/EMeraldGeo/deprecated-examples-Clustering/blob/master/aem_inv_xyz.py

import pandas as pd
import numpy as np
import re
try:
    import projnames
except:
    projnames = None
from . import transforms
from . import alc


_RE_FLOATS = re.compile(r"^ *([-+]?[0-9]*(\.[0-9]*)?([eE][-+]?[0-9]+)?)(\s+[-+]?[0-9]*(\.[0-9]*)?([eE][-+]?[0-9]+)?)*$")
_RE_INTS = re.compile(r"^ *([-+]?[0-9]+)(\s+[-+]?[0-9]+)*$")
_RE_FLOAT = re.compile(r"^[-+]?[0-9]*(\.[0-9]*)?([eE][-+]?[0-9]+)?$")
_RE_INT = re.compile(r"^[-+]?[0-9]+$")

# We match these types of column names for layer data:
#   rho_i[6]
#   rho_i(6)
#   rho_i_6
#   rho_i6
# Previously we did not match numbered columns without a separator before the suffix (e.g., rho_i6), but changed this
# on 2022-08-30. We do a check to catch single layer columns with a numerical suffix now with the function
# _transfer_per_location_cols_with_numerical_suffix.
# There may be lingering issues with the naming convention used in Aaarhus Workbench / ALC files.
_RE_LAYER_COL = re.compile(r"^(.*?)[(_\[]?([0-9]+)[)\]]?$")

_NA_VALUES = ["", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN", "<NA>",
             "N/A", "NA", "NULL", "NaN", "n/a", "nan", "null", "*"]

def _transfer_per_location_cols_with_numerical_suffix(colgroups, per_sounding_cols):
    """
    Search through the dictionary colgroups. If any list of columns has a length of only 1, parse this as a
    per-sounding columns instead, and transfer columns to the list per_sounding_cols.

    @param colgroups: dicitonary of group_name (str) on keys and group columns (list) as values
    @param per_sounding_cols: list of columns to parse as per-souding locations
    @return: modified colgroups and per_sounding_cols
    """
    groups_to_delete = []
    for group_name, group_cols in colgroups.items():
        if len(group_cols) < 2:
            per_sounding_cols += group_cols
            groups_to_delete.append(group_name)
    for group_name in groups_to_delete: colgroups.pop(group_name)
    return colgroups, per_sounding_cols

def _split_layer_columns(df):
    per_layer_cols = [col for col in df.columns if re.match(_RE_LAYER_COL, col)]
    per_sounding_cols = [col for col in df.columns if not col in per_layer_cols]

    colgroups = {}
    for col in per_layer_cols:
        group = re.match(_RE_LAYER_COL, col).groups()[0]
        if group not in colgroups: colgroups[group] = []
        colgroups[group].append(col)

    colgroups, per_sounding_cols = _transfer_per_location_cols_with_numerical_suffix(colgroups, per_sounding_cols)

    def columns_to_layers(columns):
        layers = np.array([int(re.match(_RE_LAYER_COL, col).groups()[1]) for col in columns])
        layers -= np.min(layers)
        return dict(zip(columns, layers))
        
    colgroups = {key.strip("_"):
                 df[columns].rename(
                     columns = columns_to_layers(columns))
                 for key, columns in colgroups.items()}

    return df[per_sounding_cols], colgroups

def _parse(inputfile, source=None, alcfile=None, **kw):
    headers = {}
    
    name = None
    col_names = None

    for idx, line in enumerate(inputfile):
        if not line.startswith("/"):
            raise Exception("Unknown header line or end of header not recognized")
        if name is None and line.startswith("/ "):
            col_names = [value.lower()
                         for value in line[1:].strip().split(' ')
                         if value != '']
            break            
        
        line = line[1:].strip()

        if line == 'HEADER:':
            continue
        
        if line.startswith("Number of gates for channel"):
            channel_nr=line.split("is")[0].split()[-1]  
            headerword="Number of gates for channel {}".format(channel_nr).lower()
            headers[headerword] = line.split()[-1]
            name = None
        elif line.startswith("Gates for channel"):
            channel_nr=line.split(":")[0].split()[-1]
            headerword="Gate times for channel {}".format(channel_nr).lower()
            headers[headerword] = line.split(": ")[-1]
            name = None
        elif name is None:
            name = line.lower()
        else:
            headers[name] = line
            name = None

    na_values = _NA_VALUES
    if "dummy" in headers:
        na_values + na_values + [headers["dummy"]]
    full_df = pd.read_csv(inputfile, sep= '\s+', names = col_names, na_values=na_values, engine = 'python')

    for key, value in headers.items():
        if " " in value and re.match(_RE_INTS, value):
            headers[key] = [int(item) for item in re.split(r"\s+", value)]
        elif " " in value and re.match(_RE_FLOATS, value):
            headers[key] = [float(item) for item in re.split(r"\s+", value)]
        elif value and re.match(_RE_FLOAT, value):
            headers[key] = float(value)
        elif re.match(_RE_INT, value):
            headers[key] = int(value)            

    alcdata = None
    if alcfile is not None:
        alcdata = alc.parse(alcfile, full_df.columns)
        mapping = alcdata["mapping"].loc[alcdata["mapping"].position >= 0]
        mapping = mapping.set_index("column")["canonical_name"].to_dict()
        full_df = full_df.rename(columns=mapping)
        
    df, layer_dfs = _split_layer_columns(full_df)

    headers["source"] = source

    res = {"flightlines": df,
            "layer_data": layer_dfs,
            "model_info": headers,
            "file_meta": {"columns": full_df.columns}}

    if alcdata is not None:
        res["alc_info"] = alcdata["meta"]
    
    return res
    
def parse(nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'r') as f:
            return _parse(f, source=nameorfile, **kw)
    else:
        return _parse(nameorfile, **kw)

def _un_split_layer_columns(data):
    data=data.copy()
    flightlines= data[list(data.keys())[0]]
    dic={}
    for key, value in data['layer_data'].items():
        dic[key] = value
        dic[key].columns= [key + '[' + str(col) + ']' for col in dic[key].columns]
    merge_layers = pd.concat(dic.values(), axis=1)
    merge_dfs= pd.concat((flightlines, merge_layers), axis=1)
    return merge_dfs

def _dump(data, file, alcfile=None):
    df = _un_split_layer_columns(data)
    for key, value in data['model_info'].items():
        if key != 'source':
            file.write("/" + str(key) + "\n")
            if isinstance(value, list):
                file.write("/" + ' '.join(str(item) for item in value) + "\n")
            else:
                file.write("/" + str(value) + "\n")
    file.write('/ ')
    df.to_csv(file, index=False, sep=' ', na_rep="*", encoding='utf-8')

    if alcfile is not None:
        alc.dump(data, alcfile, columns=df.columns)

def dump(data, nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'w') as f:
            return _dump(data, f, **kw)
    else:
        return _dump(data, f, **kw)



_dump_function = dump

class XYZ(object):
    def __new__(cls, *arg, **kw):
        self = object.__new__(cls)
        if arg or kw:
            if arg and isinstance(arg[0], dict):
                self.model_dict = arg[0]
            else:
                self.model_dict = parse(*arg, **kw)
        return self

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
        layer_constants = pd.DataFrame(index=next(iter(layer_dfs.values())).columns)
        for key, layer_df in layer_dfs.items():
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
        for colname in ("x", "utmx"):
            if colname in self.flightlines.columns:
                return colname
    @property
    def y_column(self):
        for colname in ("y", "utmy"):
            if colname in self.flightlines.columns:
                return colname
            
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
            repr(self.flightlines[[self.x_column, self.y_column]].describe().loc[["min", "max"]]),
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
