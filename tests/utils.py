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
