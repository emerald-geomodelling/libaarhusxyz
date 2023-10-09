import pandas as pd
import msgpack
import msgpack_numpy as m
m.patch()

from . import geojson

def coerce(s):
    if s.dtype != "O":
        return s
    try:
        return s.astype(float)
    except:
        return s

def df2dict(df):
    return {col: coerce(df[col]).values for col in df.columns}

def dfs2dict(d):    
    if isinstance(d, dict):
        return {key: dfs2dict(value) for key, value in d.items()}
    elif isinstance(d, pd.DataFrame):
        return df2dict(d)
    else:
        return d

def _dump(model, f, gex=None):
    data = dict(model.model_dict)
    if gex is not None:
        data["system"] = gex.gex_dict
    data["geojson"] = geojson.to_geojson(model)    
    data = dfs2dict(data)
    msgpack.dump(data, f)

def dump(model, nameorfile, gex=None):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'wb') as f:
            _dump(model, f, gex=gex)
    else:
        _dump(model, nameorfile, gex=gex)
