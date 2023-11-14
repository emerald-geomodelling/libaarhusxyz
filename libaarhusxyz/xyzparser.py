# Originally from https://github.com/EMeraldGeo/deprecated-examples-Clustering/blob/master/aem_inv_xyz.py

import pandas as pd
import numpy as np
import copy
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
# As of 2022-09-05, We also check for columns that have a numerical suffix but no separator like this:
#   rho_i6
# We treat these cases as "ambiguous", and they are treated differenly than the three other cases above. See more in the
# function _transfer_per_location_cols_with_numerical_suffix.
_RE_LAYER_COL_WITH_SEPARATOR = re.compile(r"^(.*?)[(_\[]([0-9]+)[)\]]?$")
_RE_ALL_NUMBERED_COL = re.compile(r"^(.*?)[(_\[]?([0-9]+)[)\]]?$")

_NA_VALUES = ["", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN", "<NA>",
             "N/A", "NA", "NULL", "NaN", "n/a", "nan", "null", "*"]

def _transfer_per_location_cols_with_numerical_suffix(colgroups, per_sounding_cols, ambiguous_groups):
    """
    Search through the dictionary colgroups. If any list of columns has a length of only 1, parse this as a
    per-sounding columns instead, and transfer columns to the list per_sounding_cols.

    For the groups listed in "ambiguous_groups", we do an extra check because their numerical suffix is not separated
    with an extra '[]', '()', or '_' (.e.g, 'rho_i6','Misc1', 'Current_Ch01', 'Current_Ch02'). These ones are transfered
     to per_sounding_cols if they have:
        a. a length of less than 3, or
        b. end in "Ch", "CH", or "ch" (usually a column for data about a channel rather than data sampled in
         depth or time)

    @param colgroups: dicitonary of group_name (str) on keys and group columns (list) as values
    @param per_sounding_cols: list of columns to parse as per-souding locations
    @param ambiguous_groups: list of groups whose columns have a numerical suffix but no separator (e.g. "rho_i_std" for
     columns ['rho_i_std1', 'rho_i_std2', ...])
    @return: modified colgroups and per_sounding_cols
    """
    groups_to_delete = []
    for group_name, group_cols in colgroups.items():
        if len(group_cols) < 2:
            per_sounding_cols += group_cols
            groups_to_delete.append(group_name)
        elif group_name in ambiguous_groups and (len(group_cols) < 3 or group_name[-2:].lower() == "ch"):
            per_sounding_cols += group_cols
            groups_to_delete.append(group_name)

    for group_name in groups_to_delete: colgroups.pop(group_name)
    return colgroups, per_sounding_cols

def _split_layer_columns(df):
    per_layer_cols = [col for col in df.columns if re.match(_RE_LAYER_COL_WITH_SEPARATOR, col)]

    all_numbered_cols = [col for col in df.columns if re.match(_RE_ALL_NUMBERED_COL, col)]
    ambiguous_cols = [col for col in all_numbered_cols if col not in per_layer_cols]

    per_sounding_cols = [col for col in df.columns if (not col in per_layer_cols) and (not col in ambiguous_cols)]

    colgroups = {}
    for col in per_layer_cols:
        match = re.match(_RE_LAYER_COL_WITH_SEPARATOR, col)
        if not match: continue
        group = match.groups()[0]
        if group not in colgroups: colgroups[group] = []
        colgroups[group].append(col)

    ambiguous_groups = []
    for col in ambiguous_cols:
        match = re.match(_RE_ALL_NUMBERED_COL, col)
        if not match: continue
        group = match.groups()[0]
        if group not in colgroups:
            colgroups[group] = []
            ambiguous_groups.append(group)
        colgroups[group].append(col)

    colgroups, per_sounding_cols = _transfer_per_location_cols_with_numerical_suffix(colgroups, per_sounding_cols, ambiguous_groups)

    def columns_to_layers(columns):
        matches = [re.match(_RE_ALL_NUMBERED_COL, col) for col in columns]
        layers = np.array([int(match.groups()[1]) if match else -1 for match in matches])
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

    while True:
        pos = inputfile.tell()
        line = inputfile.readline()
        
        if not line:
            raise EOFError("End of file reached while still reading header lines")
        
        if not line.startswith("/"):
            inputfile.seek(pos)
            break

        if re.match(r"^/(([\s=]*)|([\s-]*))$", line):
            # Lines line / ======== ======== ======== are just dividers in some files
            continue

        if line.startswith("/ "):
            # Always set this, so we use the last one
            col_names = [value.lower().strip(",")
                         for value in line[1:].strip().split(' ')
                         if value != '']
        
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
    full_df = pd.read_csv(inputfile, sep = ",?[\s]+", names = col_names, na_values=na_values, engine = 'python')

    line_separators = (full_df[full_df.columns[0]] == "Line") | (full_df[full_df.columns[0]] == "Tie")
    if full_df[full_df.columns[0]].dtype == "O":
        comments = full_df[full_df.columns[0]].str.match(r"^\s*/")
    else:
        comments = full_df.index != full_df.index
    full_df = full_df.loc[~line_separators & ~comments].reset_index(drop=True).copy()

    cols = full_df.columns
    for c in cols:
        try:
            full_df[c] = pd.to_numeric(full_df[c])
        except:
            pass
    
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
            "file_meta": {"columns": list(full_df.columns)}}

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
    if len(data['layer_data']) == 0:
        return data['flightlines']
    data=data.copy()
    flightlines= data['flightlines']
    dic={}
    for key, value in data['layer_data'].items():
        dic[key] = value
        dic[key].columns= [key + '_' + "{:02d}".format(col+1) for col in dic[key].columns]
    merge_layers = pd.concat(dic.values(), axis=1)
    merge_dfs= pd.concat((flightlines, merge_layers), axis=1)
    return merge_dfs

def _dump(data, file, alcfile=None):
    df = _un_split_layer_columns(data)
    for key, value in data['model_info'].items():
        if key != 'source':
            file.write(b"/" + str(key).encode('utf-8') + b"\n")
            if isinstance(value, (list, np.ndarray, pd.Series)):
                file.write(b"/" + b' '.join(str(item).encode('utf-8') for item in value) + b"\n")
            else:
                file.write(b"/" + str(value).encode('utf-8') + b"\n")
    file.write(b'/ ')
    df.to_csv(file, index=False, sep=' ', na_rep="*", encoding='utf-8')

    if alcfile is not None:
        alc.dump(data, alcfile, columns=df.columns)

def dump(data_in, nameorfile, **kw):
    data = copy.deepcopy(data_in)
    if isinstance(nameorfile, str):
        with open(nameorfile, 'wb') as f:
            return _dump(data, f, **kw)
    else:
        return _dump(data, nameorfile, **kw)


