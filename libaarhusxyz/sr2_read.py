#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  1 15:44:28 2021

@author: mp
"""

import numpy as np


def getAUXdata(headerlines):
    sr2={"header":headerlines[0]}
    words=headerlines[1].split()
    sr2["Channel#"]=words[0]
    sr2["#repititions"]=words[1]
    sr2["#datapoints"]=words[2]
    sr2["begin_date"]="-".join(words[3:6])
    sr2["begin_time"]=":".join(words[6:9])    
    sr2["end_date"]="-".join(words[10:13])
    sr2["end_time"]=":".join(words[13:16])
    return sr2


def getSystemResponse(text):
    data=[]
    for lines in text:
        numberstrings   = lines.split()
        numbers=[float(s) for s in numberstrings]
        data.append(numbers)
    return np.array(data)


def readfile(sr2_filename):
    with open(sr2_filename) as f:
        text=f.readlines()
    sr2=getAUXdata(text[:2])
    sr2["system_response"]=getSystemResponse(text[2:])
    return sr2

