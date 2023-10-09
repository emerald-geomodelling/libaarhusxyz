import unittest
import libaarhusxyz
import libaarhusxyz.export.geojson
import libaarhusxyz.export.msgpack
import io
import json
import msgpack
from utils import *

class TestExports(unittest.TestCase):
    def test_export_geojson(self):
        xyz =libaarhusxyz.XYZ(os.path.join(test_datadir_wb_5940, "pro_AVG_export.xyz"), normalize=True)
        f = io.StringIO()
        libaarhusxyz.export.geojson.dump(xyz, f)
        f.seek(0)
        geojson = json.load(f)
        assert len(geojson["features"]) == 1
        assert geojson["features"][0]["properties"]["title"] == 103401

    def test_export_msgpack(self):
        xyz = libaarhusxyz.XYZ(os.path.join(test_datadir_wb_5940, "pro_AVG_export.xyz"), normalize=True)
        f = io.BytesIO()
        libaarhusxyz.export.msgpack.dump(xyz, f)
        f.seek(0)
        data = msgpack.load(f, strict_map_key=False)
        assert (data["flightlines"]["x"] == xyz.flightlines.x).min()
        
        
