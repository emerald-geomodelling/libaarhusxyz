import unittest
import libaarhusxyz
import libaarhusxyz.normalizer
import downfile
import os.path
import pandas as pd
import numpy as np
import copy
from utils import *

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


