import pandas as pd
import numpy as np
import pyproj
import re
import projnames
import datetime

def project(innproj, utproj, xinn, yinn):
    innproj = int(innproj)
    utproj = int(utproj)
    # UTM convention is coordinate order Northing-Easting. CCh, 2020-06-18
    return pyproj.Transformer.from_crs(
        innproj, utproj, always_xy=True).transform(xinn, yinn)

def normalize_headers(model):
    headers = model.model_info
    
    if "numlayer" in headers:
        headers['number of layers'] = headers.pop("numlayer")
                
    headers["inversion_type"] = None
    if 'node name(s)' in headers:
        headers["inversion_type"] = headers['node name(s)'].split("_")[0]

def normalize_column_names(model):
    df = model.flightlines
    layer_dfs = model.layer_data
    headers = model.model_info
    
    linenocol = "line"
    if "line_no" in df.columns:
        linenocol = "line_no"

    df = df.rename(columns={
        linenocol:"title",
        "elevation":"topo",
        'doi_conservative':"doi_upper",
        'doi_standard':"doi_lower",
        'altitude_[m]': 'invalt',
        'altitude_std_[fact]': 'invaltstd',
        'altitude_a-priori_[m]': 'alt',
        'altitude_a-priori_std_[fact]': 'altstd',
        'segments': 'segment'
    })

    if "sigma" in layer_dfs: layer_dfs["sigma_i"] = layer_dfs.pop("sigma")
    if "thk" in layer_dfs: layer_dfs["height"] = layer_dfs.pop("thk")
    if "rho_i" in layer_dfs: layer_dfs["resistivity"] = layer_dfs.pop("rho_i")
    if "rho" in layer_dfs: layer_dfs["resistivity"] = layer_dfs.pop("rho")
    if "rho_i_std" in layer_dfs:
        layer_dfs["resistivity_variance_factor"] = layer_dfs.pop("rho_i_std")
    if "rho_std" in layer_dfs:
        layer_dfs["resistivity_variance_factor"] = layer_dfs.pop("rho_std")

    model.flightlines = df

def normalize_projection(model):
    headers = model.model_info
    headers["projection"] = None
    if "coordinate system" in headers:
        match = re.match(r".*\(epsg:(.*)\).*", headers["coordinate system"])
        if match:
            headers["projection"] = int(match.groups()[0])
        else:
            name = headers["coordinate system"].lower()
            name = name.replace("wgs84", "wgs 84")
            ptn = re.compile(".*" + name.replace(" ", ".*") + ".*")
            matches = [(name, value)
                       for name, value in projnames.projections.items()
                       if ptn.match(name.lower())]
            if matches:
                # NOTE: Sometimes the projection given does not
                # specify N or S for UTM zones... We are forced to
                # choose one here quite arbitrarily... This is why we
                # should use EPSG codes kids!
                headers["projection"] = matches[0][1]

def normalize_coordinates(model, project_crs=None):
    df = model.flightlines
    headers = model.model_info
    
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

    if project_crs is None:
        project_crs = headers["projection"]

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

def add_defaults(model, required_columns):
    layer_dfs = model.layer_data
    df = model.flightlines

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

def normalize(model, project_crs=None, required_columns = ['resdata',"restotal", "numdata"]):
    """This function
         * Normalizes naming and format to our internal format
         * Reprojects coordinates
         * Calculates xdist
         * Calculate z coordinates
         * Add missing columns (filled with NaNs)
    """

    normalize_headers(model)
    normalize_column_names(model)
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
