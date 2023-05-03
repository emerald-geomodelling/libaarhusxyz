import pandas as pd
import numpy as np
import pyproj
import re
import datetime
import csv
import pkg_resources

def _read_csv(f):
    return pd.read_csv(f)

with pkg_resources.resource_stream("libaarhusxyz", "normalizer.csv") as f:
    name_mapping = _read_csv(f)

def complete_name_mapping(name_mapping):
    """Fill in missing values in the name mapping using other rows in the
    mapping."""
    for col in name_mapping.columns:
        if col == "libaarhusxyz": continue
        fromfilt = ~name_mapping["alc"].isna() & ~name_mapping["libaarhusxyz"].isna()
        mapping = name_mapping.loc[fromfilt].set_index("libaarhusxyz")["alc"]
        tofilt = name_mapping["alc"].isna() & name_mapping.libaarhusxyz.isin(mapping.index)
        name_mapping.loc[tofilt, "alc"] = mapping.loc[
            name_mapping.loc[tofilt, "libaarhusxyz"]].values

complete_name_mapping(name_mapping)
    
with pkg_resources.resource_stream("libaarhusxyz", "normalizer_pattern.csv") as f:
    name_mapping_patterns = _read_csv(f)

def map_name_pattern(value):
    for idx, row in name_mapping_patterns.iterrows():
        if re.match(row.pattern, value):
            return re.sub(row.pattern, row.replacement, value)
    return value
    
def get_name_mapper(naming_standard="libaarhusxyz"):
    mapper = name_mapping.melt(naming_standard, var_name="naming_standard", value_name="src_name")
    mapper = mapper.loc[~mapper.src_name.isna()]
    mapper["src_name"] = mapper["src_name"].str.lower()
    mapper = mapper.set_index("src_name")[naming_standard]
    mapper = mapper[~mapper.index.duplicated(keep='first')]
    mapper = mapper.loc[~pd.isnull(mapper)]
    def mapperfn(name):
        newname = map_name_pattern(name)
        lnewname = newname.lower()
        if lnewname in mapper.index:
            newname = mapper.loc[lnewname]
        return newname
    return mapperfn

default_name_mapper = get_name_mapper()

def project(innproj, utproj, xinn, yinn):
    innproj = int(innproj)
    utproj = int(utproj)
    # UTM convention is coordinate order Northing-Easting. CCh, 2020-06-18
    return pyproj.Transformer.from_crs(
        innproj, utproj, always_xy=True).transform(xinn, yinn)

def normalize_headers(model, naming_standard="libaarhusxyz"):
    headers = model.model_info

    mapper = get_name_mapper(naming_standard)
    for name in list(headers.keys()):
        headers[mapper(name)] = headers.pop(name)                
            
    headers["inversion_type"] = None
    if 'node name(s)' in headers:
        headers["inversion_type"] = headers['node name(s)'].split("_")[0]

def normalize_column_names(model, naming_standard="libaarhusxyz"):
    df = model.flightlines
    layer_dfs = model.layer_data
    headers = model.model_info
     
    mapper = get_name_mapper(naming_standard)
    df.columns = [mapper(name) for name in df.columns]

    for name in list(layer_dfs.keys()):
        layer_dfs[mapper(name)] = layer_dfs.pop(name)
        
    model.flightlines = df

def normalize_projection(model):
    # Import here and not at top of file, as this is slow to import...
    import projnames
    
    headers = model.model_info
    headers["projection"] = None
    if "coordinate system" in headers:
        match = projnames.search(headers["coordinate system"])
        if match is not None:
            headers["projection"] = match

def normalize_coordinates(model, project_crs=None):
    df = model.flightlines
    headers = model.model_info
    
    if project_crs is None:
        project_crs = headers["projection"]

    if project_crs is None:
        return

    xcol = "x"
    ycol = "y"
    if "utmx" in df.columns:
        xcol = "utmx"
        ycol = "utmy"
    if "lon" in df.columns:
        headers["projection"] = 4326
        xcol = "lon"
        ycol = "lat"

    df = df.rename(columns={
        xcol:"x_orig",
        ycol:"y_orig"})
        
    df["x"], df["y"] = project(headers["projection"], project_crs, df["x_orig"].values, df["y_orig"].values)
    df["x_web"], df["y_web"] = project(headers["projection"], 3857, df["x_orig"].values, df["y_orig"].values)
    df["lon"], df["lat"] = project(headers["projection"], 4326, df["x_orig"].values, df["y_orig"].values)
    
    model.flightlines = df

def calculate_xdist(model):
    df = model.flightlines

    df["prevdist"] = np.append(
        [0],
        np.sqrt(  (df["x"].values[1:] - df["x"].values[:-1])**2
                + (df["y"].values[1:] - df["y"].values[:-1])**2))
    df.loc[np.append([False], df["title"].values[1:] != df["title"].values[:-1]), "prevdist"] = 0
    df["xdist"] = df.groupby(df["title"])["prevdist"].cumsum()
    del df["prevdist"]

REQUIRED_COLUMNS = ['resdata',"restotal", "numdata"]
def add_defaults(model, required_columns=None):
    layer_dfs = model.layer_data
    df = model.flightlines

    if required_columns is None:
        required_columns = REQUIRED_COLUMNS
    
    if "doi_lower" not in df.columns:
        df['doi_lower'] = np.full(len(df), 500, dtype=int)

    if "doi_upper" not in df.columns:
        df['doi_upper'] = np.full(len(df), 300, dtype=int)

    for col in required_columns:
        if col not in df.columns:
            df[col] = np.nan

    # Fix layer attribute tables to apply to all layers (often missing for last layer)
    NLayers = np.array([ldf.columns.max() for ldf in layer_dfs.values()]).max()
    for key, ldf in layer_dfs.items():
        for i in range(ldf.columns.max() + 1, NLayers + 1):
            ldf[i] = np.NaN

    if "resistivity_variance_factor" not in layer_dfs:
        ldf = next(iter(layer_dfs.values()))
        layer_dfs["resistivity_variance_factor"] = np.nan*ldf
        layer_dfs["doi_layer"] = ldf*0 + 2
        layer_dfs["height"] = ldf*0 + 50
        layer_dfs["z_bottom"] = ldf*0 + 500

            
def normalize_depths(model):
    layer_dfs = model.layer_data
    if "dep_bot" in layer_dfs:
        layer_dfs["dep_bot"] = layer_dfs["dep_bot"].fillna(np.Inf)
        if 'dep_top' in layer_dfs.keys():
            layer_dfs["dep_top"] = layer_dfs["dep_top"].fillna(np.Inf)
        else:
            layer_dfs["dep_top"] = layer_dfs["dep_bot"].shift(1,axis=1)
            layer_dfs["dep_top"].iloc[:,0]=0.0

def calculate_z(model):
    df = model.flightlines
    layer_dfs = model.layer_data
    if "dep_bot" in layer_dfs:
        layer_dfs["z_bottom"] = np.meshgrid(layer_dfs["dep_bot"].columns, df["topo"])[1] - layer_dfs["dep_bot"]
        layer_dfs["z_top"] = np.meshgrid(layer_dfs["dep_top"].columns, df["topo"])[1] - layer_dfs["dep_top"]

def calculate_height(model):
    layer_dfs = model.layer_data
    if "dep_bot" in layer_dfs and 'height' not in layer_dfs.keys():
        layer_dfs["height"] = layer_dfs["dep_bot"] - layer_dfs["dep_top"]

def calculate_doi_layer(model):
    df = model.flightlines
    layer_dfs = model.layer_data
    if "dep_bot" in layer_dfs:
        doi_lower = np.meshgrid(layer_dfs["dep_bot"].columns, df["doi_lower"])[1]
        doi_upper = np.meshgrid(layer_dfs["dep_bot"].columns, df["doi_upper"])[1]

        layer_dfs["doi_layer"] = pd.DataFrame(
            np.where(layer_dfs["dep_bot"] > doi_lower,
                     2,
                     np.where(layer_dfs["dep_bot"] > doi_upper,
                              1, 0)), columns=layer_dfs["dep_bot"].columns)


def normalize_dates(model):
    if "date" in model.flightlines.columns and "time" in model.flightlines.columns:
        datestr = model.flightlines.date.fillna("").astype(str)
        timestr = model.flightlines.time.fillna("").astype(str)
        datetimestr = np.where(datestr != "", datestr + " " + timestr, "")
        
        model.flightlines = model.flightlines.assign(
            timestamp = pd.Series(pd.to_datetime(datetimestr) - datetime.datetime(1900,1,1)).dt.total_seconds() / (24 * 60 * 60)
        ).drop(
            columns = ["date", "time"])

def normalize_nans(model, nan_value=None):
    if nan_value is None:
        if 'dummy' in model.model_info.keys():
            nan_value = model.model_info['dummy']
        else:
            nan_value='*'
        
    for col in model.flightlines.columns:
        filt=model.flightlines[col]==nan_value
        model.flightlines.loc[filt,col]=np.nan
    
    for key in model.layer_data.keys():
        filt=model.layer_data[key]==nan_value
        model.layer_data[key][filt]=np.nan

    # FIXME: Convert column types from O here?
        
def normalize_naming(model, naming_standard="libaarhusxyz"):
    normalize_headers(model, naming_standard)
    normalize_column_names(model, naming_standard)
        
def normalize(model, project_crs=None, required_columns=None, naming_standard="libaarhusxyz", nan_value=None):
    """This function
         * Normalizes naming and format to our internal format
         * Replaces * with NaN:s
         * Reprojects coordinates
         * Calculates xdist
         * Calculate z coordinates
         * Add missing columns (filled with NaNs)
    """

    normalize_naming(model, naming_standard)

    normalize_nans(model, nan_value)
    normalize_projection(model)
    normalize_coordinates(model, project_crs)
    normalize_dates(model)
    
    calculate_xdist(model)
    add_defaults(model, required_columns)
    normalize_depths(model)
    calculate_z(model)
    calculate_height(model)
    calculate_doi_layer(model)
    
    return model
