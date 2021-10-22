import pandas as pd
import numpy as np


def normalize_layer_depths(data):
    """Normalizes all layer depths, so that layer X is at the same depth
    in all soundings. This is done by upsampling all soundings to a
    set of layers with boundaries (top and bottom) being the union of
    all boundaries from all the soundings. Note that this is just pure
    upsampling, not interpolation.
    """
    d_bot = data["layer_data"]["dep_bot"]
    groups = data["layer_data"]["dep_top"].groupby(by=list(data["layer_data"]["dep_top"].columns)).groups

    unique_depths = np.unique(d_bot.values.flatten())
    u_d = pd.DataFrame({"unique": pd.Series(unique_depths)})

    res_layer_data = {param: pd.DataFrame(index=data["layer_data"][param].index,
                                          columns=np.arange(len(u_d.unique)))
                      for param in data["layer_data"].keys()}

    for g1 in groups.values():
        g1_boundaries = pd.DataFrame({"top": data["layer_data"]["dep_top"].loc[g1].iloc[0],
                                      "bot": data["layer_data"]["dep_bot"].loc[g1].iloc[0]}).fillna(np.inf)
        for dest_layer, (top, bot) in enumerate(zip([0] + list(u_d.unique), list(u_d.unique))):
            source_layer = g1_boundaries.index[(g1_boundaries.top <= top) & (g1_boundaries.bot >= bot)][0]
            
            for param in res_layer_data.keys():
                if param in ("dep_top", "dep_bot"):
                    continue
                if source_layer not in data["layer_data"][param].columns:
                    param_data = np.nan
                else:
                    param_data = data["layer_data"][param].loc[g1, source_layer]
                res_layer_data[param].loc[g1, dest_layer] = param_data
            res_layer_data["dep_top"].loc[g1, dest_layer] = top
            res_layer_data["dep_bot"].loc[g1, dest_layer] = bot

    data = dict(data)
    data["layer_data"] = res_layer_data
    return data
