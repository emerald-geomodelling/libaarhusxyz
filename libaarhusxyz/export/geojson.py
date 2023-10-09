import geopandas as gpd
import shapely.geometry.linestring
import json


def to_geojson_str(model):
    xy = gpd.points_from_xy(
        model.flightlines.x_web, 
        model.flightlines.y_web,
        crs = 3857)
    points = gpd.GeoDataFrame(model.flightlines.copy(), geometry = xy)
    lines = points.groupby(model.line_id_column)['geometry'].apply(
        lambda x: shapely.geometry.linestring.LineString(x.tolist()))
    # Maybe we want average here, or last, also? Not sure what's most useful...
    lines = gpd.GeoDataFrame(points.groupby(model.line_id_column).first(), geometry=lines).reset_index()
    return lines.to_json()

def to_geojson(model):
    return json.loads(to_geojson_str(model))

def _dump(model, f):
    f.write(
        to_geojson_str(model))

def dump(model, nameorfile):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'w') as f:
            _dump(model, f)
    else:
        _dump(model, nameorfile)
 
