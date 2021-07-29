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

    # Note: layer - 1 because we label layers 0..NLayers-1 rather than 1..NLayers
    colgroups = {key.strip("_"):
                 df[value].rename(
                     columns = {col:int(re.match("^.*?[(\[]?([0-9]+)[)\]]?$", col).groups()[0]) - 1 for col in value})
                 for key, value in colgroups.items()}

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
        
        if name is None:
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

    return {"flightlines": df,
            "layer_data": layer_dfs,
            "model_info": headers}

def parse(nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'r') as f:
            return _parse(f, source=nameorfile, **kw)
    else:
        return _parse(nameorfile, **kw)

        
