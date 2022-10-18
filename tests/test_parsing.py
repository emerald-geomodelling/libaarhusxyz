import unittest
import libaarhusxyz
import libaarhusxyz.normalizer
import downfile
import os.path
import pandas as pd
import numpy as np
import copy

test_basedir = os.path.dirname(__file__)
test_datadir_wb_5940 = os.path.join(test_basedir, "data/aarhus_workbench.5.9.4.0")

test_datadir_wb_6011 = os.path.join(test_basedir, "data/aarhus_workbench.6.0.1.1")
test_datadir_wb_6100 = os.path.join(test_basedir, "data/aarhus_workbench.6.1.0.0")
test_datadir_wb_6210 = os.path.join(test_basedir, "data/aarhus_workbench.6.2.1.0")

test_datadir_wb_6602 = os.path.join(test_basedir, "data/aarhus_workbench.6.6.0.2")
test_datadir_wb_6700 = os.path.join(test_basedir, "data/aarhus_workbench.6.7.0.0")
test_datadir_skytem = os.path.join(test_basedir, "data/skytem")

class Difference(object):
    def __init__(self, path, diff, a, b):
        self.path = path
        self.diff = diff
        self.a = a
        self.b = b
    def __str__(self):
        return "%s: %s %s %s" % (".".join([str(i) for i in self.path]), self.a, self.diff, self.b)
        
def compare(a, b, path= [], onesided = False):
    at = type(a)
    bt = type(b)
    if at is not bt:
        yield Difference(path, "not same type as", at, bt); return
    
    if isinstance(a, dict):
        ak = set(a.keys())
        bk = set(b.keys())
        mbk = ak - bk
        mak = bk - ak
        if mbk and not onesided:
            yield Difference(path, "missing in", mbk, "b")
        if mak:
            yield Difference(path, "missing in", mak, "a")
        for key in ak.intersection(bk):
            for diff in compare(a[key], b[key], path + [key], onesided):
                yield diff
    elif isinstance(a, set):
        mb = a - b
        ma = b - a
        if mb and not onesided:
            yield Difference(path, "missing in", mb, "b")
        if ma:
            yield Difference(path, "missing in", ma, "a")
    elif isinstance(a, list):
        if len(a) != len(b):
            yield Difference(path, "not same length", len(a), len(b))
        for idx, (ai, bi) in enumerate(zip(a, b)):
            for diff in compare(ai, bi, path + [idx], onesided):
                yield diff
    elif isinstance(a, (pd.Index, pd.Series)):
        if len(a) != len(b) and not onesided:
            yield Difference(path, "not same length", len(a), len(b))
        sa = set(a)
        sb = set(b)
        msb = sa - sb
        msa = sb - sa
        if msb and not onesided:
            yield Difference(path, "missing in", msb, "b")
        if msa:
            yield Difference(path, "missing in", msa, "a")     
    elif isinstance(a, pd.DataFrame):
        for diff in compare(a.columns, b.columns, path+["columns"], onesided):
            yield diff
        for diff in compare(a.index, b.index, path+["columns"], onesided):
            yield diff
        for col in set(a.columns).intersection(b.columns):
            merged = a.loc[
                a.index.isin(b.index), [col]
            ].rename(
                columns={col: "a"}
            ).join(
                b.loc[b.index.isin(a.index), [col]].rename(
                columns={col: "b"}
            ))
            merged = merged.loc[(merged.a != merged.b) & ~(pd.isnull(merged.a) & pd.isnull(merged.b))]
            
            for diff in compare(merged.a, merged.b, path + [col], onesided):
                yield diff
    else:
        if a != b and not (pd.isnull(a) and pd.isnull(b)):
            yield Difference(path, "!=", a, b)    

class TestSkytem(unittest.TestCase):
    def test_202202(self):
        parsed = libaarhusxyz.XYZ(os.path.join(test_datadir_skytem, "2022.02.test.xyz"),
                                  alcfile=os.path.join(test_datadir_skytem, "2022.02.test.alc")).model_dict
        fixture = downfile.parse(os.path.join(test_datadir_skytem, "2022.02.test.down"))
        del parsed["model_info"]["source"]
        del fixture["model_info"]["source"]

        for diff in compare(parsed, fixture):
            self.fail(str(diff))

class TestAarhusWorkbench6602(unittest.TestCase):
    def test_raw(self):
        parsed = libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6602, "RAW_export_example_averagde_data_export.xyz")).model_dict
        fixture = downfile.parse(os.path.join(test_datadir_wb_6602, "RAW_export_example_averagde_data_export.down"))
        del parsed["model_info"]["source"]
        del fixture["model_info"]["source"]

        for diff in compare(parsed, fixture):
            self.fail(str(diff))

    def test_avg(self):
        parsed = libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6602, "AVG_export_example_averagde_data_export.xyz")).model_dict
        fixture = downfile.parse(os.path.join(test_datadir_wb_6602, "AVG_export_example_averagde_data_export.down"))
        del parsed["model_info"]["source"]
        del fixture["model_info"]["source"]

        for diff in compare(parsed, fixture):
            self.fail(str(diff))

    def test_sci_dat(self):
        parsed = libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6602, "SCI_1_Pro3_MOD_dat_example_SCI_inversion_export.xyz")).model_dict
        fixture = downfile.parse(os.path.join(test_datadir_wb_6602, "SCI_1_Pro3_MOD_dat_example_SCI_inversion_export.down"))
        del parsed["model_info"]["source"]
        del fixture["model_info"]["source"]

        for diff in compare(parsed, fixture):
            self.fail(str(diff))

    def test_sci_inv(self):
        parsed = libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6602, "SCI_1_Pro3_MOD_inv_example_SCI_inversion_export.xyz")).model_dict
        fixture = downfile.parse(os.path.join(test_datadir_wb_6602, "SCI_1_Pro3_MOD_inv_example_SCI_inversion_export.down"))
        del parsed["model_info"]["source"]
        del fixture["model_info"]["source"]

        for diff in compare(parsed, fixture):
            self.fail(str(diff))

    def test_sci_syn(self):
        parsed = libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6602, "SCI_1_Pro3_MOD_syn_example_SCI_inversion_export.xyz")).model_dict
        fixture = downfile.parse(os.path.join(test_datadir_wb_6602, "SCI_1_Pro3_MOD_syn_example_SCI_inversion_export.down"))
        del parsed["model_info"]["source"]
        del fixture["model_info"]["source"]

        for diff in compare(parsed, fixture):
            self.fail(str(diff))

class TestAarhusWorkbenchVersion(unittest.TestCase):
    metadata_raw = {'model_info': {'data unit', 'number of gates for channel 2', 'number of gates for channel 1', 'gate times for channel 1', 'dummy', 'info', 'data type', 'source', 'inversion_type', 'gate times for channel 2', 'workspace name', 'wb version', 'coordinate system', 'node name(s)', 'projection'},
                    'flightlines': {'lon', 'title', 'fieldpolarity', 'numgates', 'rx_altitude_std', 'x', 'restotal', 'x_orig', 'lat', 'current', 'timestamp', 'y', 'y_orig', 'x_web', 'tx_altitude', 'resdata', 'channel_no', 'doi_lower', 'doi_upper', 'tx_area', 'y_web', 'tilt_x_std', 'numdata', 'rx_altitude', 'tilt_y_std', 'tx_altitude_std', 'topo', 'tilt_y', 'xdist', 'tilt_x'},
                    'layer_data': {'dbdt_std_ch1gt', 'dbdt_ch1gt', 'height', 'doi_layer', 'dbdt_inuse_ch2gt', 'z_bottom', 'dbdt_inuse_ch1gt', 'resistivity_variance_factor', 'dbdt_std_ch2gt', 'dbdt_ch2gt'}}

    metadata_avg = {'model_info': {'info', 'projection', 'workspace name', 'node name(s)', 'data unit', 'dummy', 'gate times for channel 1', 'data type', 'source', 'number of gates for channel 1', 'inversion_type', 'gate times for channel 2', 'coordinate system', 'wb version', 'number of gates for channel 2'},
                    'flightlines': {'tx_altitude_std', 'fieldpolarity', 'x', 'tx_altitude', 'y', 'x_web', 'numdata', 'tilt_x_std', 'rx_altitude_std', 'restotal', 'lat', 'topo', 'tilt_y_std', 'tx_area', 'resdata', 'title', 'x_orig', 'channel_no', 'tilt_x', 'timestamp', 'lon', 'xdist', 'rx_altitude', 'numgates', 'doi_lower', 'y_web', 'y_orig', 'doi_upper', 'tilt_y', 'current'},
                    'layer_data': {'resistivity_variance_factor', 'dbdt_ch2gt', 'dbdt_ch1gt', 'doi_layer', 'dbdt_inuse_ch2gt', 'dbdt_inuse_ch1gt', 'height', 'dbdt_std_ch2gt', 'dbdt_std_ch1gt', 'z_bottom'}}

    metadata_dat = {'model_info': {'length unit', 'info', 'gate times (s)', 'wb version', 'workspace name', 'model unit', 'data unit', 'number of gates', 'number of layers', 'source', 'dummy', 'coordinate system', 'inversion_type', 'node name(s)', 'data type', 'projection'},
                    'flightlines': {'lon', 'fid', 'invtilt', 'doi_upper', 'y_orig', 'doi_lower', 'restotal', 'resdata', 'x_orig', 'record', 'topo', 'title', 'tilt', 'invaltstd', 'xdist', 'x_web', 'invalt', 'alt', 'y_web', 'x', 'timestamp', 'y', 'segment', 'deltaalt', 'invtiltstd', 'numdata', 'lat'},
                    'layer_data': {'height', 'datastd', 'data', 'z_bottom', 'doi_layer', 'resistivity_variance_factor'}}

    metadata_inv = {'model_info': {'length unit', 'info', 'gate times (s)', 'wb version', 'workspace name', 'model unit', 'data unit', 'number of gates', 'number of layers', 'source', 'dummy', 'coordinate system', 'inversion_type', 'node name(s)', 'data type', 'projection'},
                    'flightlines': {'lon', 'fid', 'invtilt', 'doi_upper', 'y_orig', 'doi_lower', 'restotal', 'resdata', 'x_orig', 'record', 'topo', 'title', 'tilt', 'invshift', 'invaltstd', 'xdist', 'x_web', 'invalt', 'alt', 'y_web', 'x', 'timestamp', 'shift', 'segment', 'invshiftstd', 'deltaalt', 'y', 'invtiltstd', 'numdata', 'lat'},
                    'layer_data': {'dep_bot_std', 'thk_std', 'height', 'dep_bot', 'dep_top', 'z_bottom', 'resistivity', 'doi_layer', 'z_top', 'resistivity_variance_factor', 'sigma_i'}}

    metadata_syn = {'model_info': {'length unit', 'info', 'gate times (s)', 'wb version', 'workspace name', 'model unit', 'data unit', 'number of gates', 'number of layers', 'source', 'dummy', 'coordinate system', 'inversion_type', 'node name(s)', 'data type', 'projection'},
                    'flightlines': {'lon', 'fid', 'invtilt', 'doi_upper', 'y_orig', 'doi_lower', 'restotal', 'resdata', 'x_orig', 'record', 'topo', 'title', 'tilt', 'invaltstd', 'xdist', 'x_web', 'invalt', 'alt', 'y_web', 'x', 'timestamp', 'y', 'segment', 'deltaalt', 'invtiltstd', 'numdata', 'lat'},
                    'layer_data': {'height', 'data', 'z_bottom', 'doi_layer', 'resistivity_variance_factor'}}

    
    def extract_metadata(self, xyz):
        return {"model_info": set(xyz.model_info.keys()),
                "flightlines": set(xyz.flightlines.columns),
                "layer_data": set(xyz.layer_data.keys())}

    def assertDeepEqual(self, a, b):
        for diff in compare(a, b):
            self.fail(str(diff))
            
    def assertDeepSupersetOf(self, a, b):
        for diff in compare(a, b, onesided=True):
            self.fail(str(diff))
    
    def compare_versions(self, wb6, wbtest):
        libaarhusxyz.normalizer.normalize(wb6)
        libaarhusxyz.normalizer.normalize(wbtest)

        wb6_keys = set(wb6.model_info.keys())
        wbtest_keys = set(wbtest.model_info.keys())
        self.assertEqual(wb6_keys, wbtest_keys)

        wbtest_cols = set(wbtest.flightlines.columns)
        wb6_cols = set(wb6.flightlines.columns)

        self.assertEqual((wb6_cols - wbtest_cols) - {'deltaalt',
                                                  'fid',
                                                  'invshift',
                                                  'invshiftstd',
                                                  'invtilt',
                                                  'invtiltstd',
                                                  'shift',
                                                  'tilt'}, set())
        self.assertEqual((wbtest_cols - wb6_cols) - {'altstd'}, set())

        wb6_ld = set(wb6.layer_data.keys())
        wbtest_ld = set(wbtest.layer_data.keys())

        self.assertEqual(wb6_ld - wbtest_ld, set())
        self.assertEqual(wbtest_ld - wb6_ld, set())


class TestAarhusWorkbench5940(TestAarhusWorkbenchVersion):
    metadata_avg = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_avg)
    metadata_avg["layer_data"] = metadata_avg["layer_data"] - {'dbdt_inuse_ch1gt', 'dbdt_inuse_ch2gt'}
    
    metadata_dat = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_dat)
    metadata_dat["model_info"] = metadata_dat["model_info"] - {'model unit', 'length unit'}
    metadata_dat["flightlines"] = metadata_dat["flightlines"] - {'timestamp', 'fid'}
    metadata_dat["layer_data"] = metadata_dat["layer_data"] - {'data', 'datastd'}
    
    metadata_inv = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_inv)
    metadata_inv["model_info"] = metadata_inv["model_info"] - {'model unit', 'length unit'}
    metadata_inv["flightlines"] = metadata_inv["flightlines"] - {'timestamp', 'fid', 'invshift', 'shift', 'invshiftstd'}
    
    metadata_syn = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_syn)
    metadata_syn["model_info"] = metadata_syn["model_info"] - {'model unit', 'length unit'}
    metadata_syn["flightlines"] = metadata_syn["flightlines"] - {'timestamp', 'fid'}
    metadata_syn["layer_data"] = metadata_syn["layer_data"] - {'data'}

    def test_avg(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_5940, "pro_AVG_export.xyz"), normalize=True)),
            self.metadata_avg)
            
    def test_sci_dat(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_5940, "pro_MOD_dat.xyz"), normalize=True)),
            self.metadata_dat)

    def test_sci_inv(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_5940, "pro_MOD_inv.xyz"), normalize=True)),
            self.metadata_inv)

    def test_sci_syn(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_5940, "pro_MOD_syn.xyz"), normalize=True)),
            self.metadata_syn)


class TestAarhusWorkbench6011(TestAarhusWorkbenchVersion):
    metadata_dat = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_dat)
    metadata_dat["model_info"] = metadata_dat["model_info"] - {'model unit', 'length unit'}
    metadata_dat["flightlines"] = metadata_dat["flightlines"] - {'timestamp', 'fid'}
    metadata_dat["layer_data"] = metadata_dat["layer_data"] - {'data', 'datastd'}
    
    metadata_inv = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_inv)
    metadata_inv["model_info"] = metadata_inv["model_info"] - {'model unit', 'length unit'}
    metadata_inv["flightlines"] = metadata_inv["flightlines"] - {'timestamp', 'fid', 'invshift', 'shift', 'invshiftstd'}
    
    metadata_syn = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_syn)
    metadata_syn["model_info"] = metadata_syn["model_info"] - {'model unit', 'length unit'}
    metadata_syn["flightlines"] = metadata_syn["flightlines"] - {'timestamp', 'fid'}
    metadata_syn["layer_data"] = metadata_syn["layer_data"] - {'data'}

    def test_sci_dat(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6011, "MOD_dat.xyz"), normalize=True)),
            self.metadata_dat)

    def test_sci_inv(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6011, "MOD_inv.xyz"), normalize=True)),
            self.metadata_inv)

    def test_sci_syn(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6011, "MOD_syn.xyz"), normalize=True)),
            self.metadata_syn)


class TestAarhusWorkbench6100(TestAarhusWorkbenchVersion):
    metadata_avg = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_avg)
    metadata_avg["model_info"] = metadata_avg["model_info"] - {'gate times for channel 2', 'number of gates for channel 2'}
    metadata_avg["layer_data"] = metadata_avg["layer_data"] - {'dbdt_inuse_ch2gt', 'dbdt_inuse_ch1gt', 'dbdt_std_ch2gt', 'dbdt_ch2gt'}

    metadata_dat = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_dat)
    metadata_dat["model_info"] = metadata_dat["model_info"] - {'model unit', 'length unit'}
    metadata_dat["flightlines"] = metadata_dat["flightlines"] - {'timestamp', 'fid'}
    metadata_dat["layer_data"] = metadata_dat["layer_data"] - {'data', 'datastd'}
    
    metadata_inv = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_inv)
    metadata_inv["model_info"] = metadata_inv["model_info"] - {'model unit', 'length unit'}
    metadata_inv["flightlines"] = metadata_inv["flightlines"] - {'timestamp', 'fid', 'invshift', 'shift', 'invshiftstd'}
    
    metadata_syn = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_syn)
    metadata_syn["model_info"] = metadata_syn["model_info"] - {'model unit', 'length unit'}
    metadata_syn["flightlines"] = metadata_syn["flightlines"] - {'timestamp', 'fid'}
    metadata_syn["layer_data"] = metadata_syn["layer_data"] - {'data'}

    def test_avg(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6100, "pronode_AVG_export.xyz"), normalize=True)),
            self.metadata_avg)
            
    def test_sci_dat(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6100, "MOD_dat.xyz"), normalize=True)),
            self.metadata_dat)

    def test_sci_inv(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6100, "MOD_inv.xyz"), normalize=True)),
            self.metadata_inv)

    def test_sci_syn(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6100, "MOD_syn.xyz"), normalize=True)),
            self.metadata_syn)

        
class TestAarhusWorkbench6210(TestAarhusWorkbenchVersion):
    metadata_avg = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_avg)
    metadata_avg["model_info"] = metadata_avg["model_info"] - {'gate times for channel 2', 'number of gates for channel 2'}
    metadata_avg["layer_data"] = metadata_avg["layer_data"] - {'dbdt_inuse_ch2gt', 'dbdt_inuse_ch1gt', 'dbdt_std_ch2gt', 'dbdt_ch2gt'}

    def test_avg(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6210, "AVG_export.xyz"), normalize=True)),
            self.metadata_avg)

        

class TestAarhusWorkbench6700(TestAarhusWorkbenchVersion):
    metadata_dat = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_dat)
    metadata_dat["flightlines"] = metadata_dat["flightlines"] - {'invtilt', 'deltaalt', 'invtiltstd', 'fid', 'tilt'}

    metadata_inv = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_inv)
    metadata_inv["flightlines"] = metadata_inv["flightlines"] - {'tilt', 'invshiftstd', 'shift', 'invshift', 'fid', 'invtilt', 'deltaalt', 'invtiltstd'}
    
    metadata_syn = copy.deepcopy(TestAarhusWorkbenchVersion.metadata_syn)
    metadata_syn["flightlines"] = metadata_syn["flightlines"] - {'tilt', 'fid', 'invtilt', 'deltaalt', 'invtiltstd'}
    
    def test_raw(self):
        self.assertDeepEqual(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6700, "RAW_export_example_raw_data_export.xyz"), normalize=True)),
            self.metadata_raw)
        
    def test_avg(self):
        self.assertDeepEqual(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6700, "AVG_export_example_averagde_data_export.xyz"), normalize=True)),
            self.metadata_avg)

    def test_sci_dat(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6700, "SCI_1_Pro3_MOD_dat_example_SCI_inversion_export.xyz"), normalize=True)),
            self.metadata_dat)

    def test_sci_inv(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6700, "SCI_1_Pro3_MOD_inv_example_SCI_inversion_export.xyz"), normalize=True)),
            self.metadata_inv)

    def test_sci_syn(self):
        self.assertDeepSupersetOf(
            self.extract_metadata(
                libaarhusxyz.XYZ(os.path.join(test_datadir_wb_6700, "SCI_1_Pro3_MOD_syn_example_SCI_inversion_export.xyz"), normalize=True)),
            self.metadata_syn)        


