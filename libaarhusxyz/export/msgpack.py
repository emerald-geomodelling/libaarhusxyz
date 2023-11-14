import pandas as pd
import numpy as np
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

def dict2dfs(d):
    if isinstance(d, dict):
        if min([isinstance(col, np.ndarray) for col in d.values()]):
            return pd.DataFrame(d)
        else:
            return {key: dict2dfs(value) for key, value in d.items()}
    else:
        return d
    
def _dump(model, f, gex=None):
    data = dict(model.model_dict)
    if gex is not None:
        data["system"] = gex.gex_dict
    if "x_web" in model.flightlines.columns:
        data["geojson"] = geojson.to_geojson(model)    
    data = dfs2dict(data)
    msgpack.dump(data, f)

def dump(model, nameorfile, gex=None):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'wb') as f:
            _dump(model, f, gex=gex)
    else:
        _dump(model, nameorfile, gex=gex)

def _load(f, return_gex=False):
    from .. import xyz
    from .. import gex
    data = msgpack.load(f, strict_map_key=False)
    data = dict2dfs(data)
    system = data.pop("system", None)
    data.pop("geojson", None)
    model = xyz.XYZ(data)
    if not return_gex:
        return model
    if system is not None:
        system = gex.GEX(system)
    return model, system

def load(nameorfile, return_gex=False):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'rb') as f:
            return _load(f, return_gex)
    else:
        return _load(nameorfile, return_gex)

