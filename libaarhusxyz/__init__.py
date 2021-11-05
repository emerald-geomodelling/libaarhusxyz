# Originally from https://github.com/EMeraldGeo/deprecated-examples-Clustering/blob/master/aem_inv_xyz.py

import pandas as pd
import numpy as np
import re

_RE_FLOATS = re.compile(r"^ *([-+]?[0-9]*(\.[0-9]*)?([eE][-+]?[0-9]+)?)(\s+[-+]?[0-9]*(\.[0-9]*)?([eE][-+]?[0-9]+)?)*$")
_RE_INTS = re.compile(r"^ *([-+]?[0-9]+)(\s+[-+]?[0-9]+)*$")
_RE_FLOAT = re.compile(r"^[-+]?[0-9]*(\.[0-9]*)?([eE][-+]?[0-9]+)?$")
_RE_INT = re.compile(r"^[-+]?[0-9]+$")

def _split_layer_columns(df):
    per_layer_cols = [col for col in df.columns if re.match(r"^.*?[(\[]?[0-9]+[)\]]?$", col)]
    per_sounding_cols = [col for col in df.columns if not col in per_layer_cols]

    colgroups = {}
    for col in per_layer_cols:
        group = re.match("^(.*?)[(\[]?[0-9]+[)\]]?$", col).groups()[0]
        if group not in colgroups: colgroups[group] = []
        colgroups[group].append(col)

    def columns_to_layers(columns):
        layers = np.array([int(re.match("^.*?[(\[]?([0-9]+)[)\]]?$", col).groups()[0]) for col in columns])
        layers -= np.min(layers)
        return dict(zip(columns, layers))
        
    colgroups = {key.strip("_"):
                 df[columns].rename(
                     columns = columns_to_layers(columns))
                 for key, columns in colgroups.items()}

    return df[per_sounding_cols], colgroups

def _parse(inputfile, source=None, **kw):
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
        
        if line.startswith("Number of gates for channel 1 is"):
            headers["Number of gates for channel 1".lower()] = line.split()[-1]
            name = None
        elif line.startswith("Number of gates for channel 2 is"):
            headers["Number of gates for channel 2".lower()] = line.split()[-1]
        elif line.startswith("Gates for channel 1"):
            headers["Gate times for channel 1".lower()] = line.split(": ")[-1]
            name = None
        elif line.startswith("Gates for channel 2"):
            headers["Gate times for channel 2".lower()] = line.split(": ")[-1]
        elif name is None:
            name = line.lower()
        else:
            headers[name] = line
            name = None
            
    df = pd.read_csv(inputfile, sep= '\s+', names = col_names, na_values=headers.get('dummy', ["", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "n/a", "nan", "null", "*"]), engine = 'python')

    for key, value in headers.items():
        if " " in value and re.match(_RE_INTS, value):
            headers[key] = [int(item) for item in re.split(r"\s+", value)]
        elif " " in value and re.match(_RE_FLOATS, value):
            headers[key] = [float(item) for item in re.split(r"\s+", value)]
        elif value and re.match(_RE_FLOAT, value):
            headers[key] = float(value)
        elif re.match(_RE_INT, value):
            headers[key] = int(value)            

    df, layer_dfs = _split_layer_columns(df)

    headers["source"] = source

    return {"flightlines": df,
            "layer_data": layer_dfs,
            "model_info": headers}

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

def _dump(data, file):
    for key, value in data['model_info'].items():
        if key != 'source':
            file.write("/" + str(key) + "\n")
            if isinstance(value, list):
                file.write("/" + ' '.join(str(item) for item in value) + "\n")
            else:
                file.write("/" + str(value) + "\n")
    file.write('/ ')
    _un_split_layer_columns(data).to_csv(file, index=False, sep=' ', encoding='utf-8')

def dump(data,nameorfile):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'w') as f:
            return _dump(data,f)
    else:
        return _dump(data,f)

        
