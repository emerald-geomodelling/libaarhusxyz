"""
Created on Fri Oct 29 11:36:28 2021

@author: mp
"""


import numpy as np




def split_sections(text):    
    sectionheaders=[]
    for line in text:
        condition = np.logical_and( ("[" in line) , ("]" in line) )
        if condition:
            sectionheaders.append(line.strip())
        
    
    sectionlineidx=[]
    linecounter=0
    for line in text:    
        for header in sectionheaders:
           if header in line:
               sectionlineidx.append(linecounter)
        linecounter=linecounter+1  
    sectionlineidx.append(len(text)+1)
    sections={"header":text[0]}
    for k in range(len(sectionheaders)):
        sections[sectionheaders[k]]=text[sectionlineidx[k]+1:sectionlineidx[k+1]-1]
    return sections, sectionheaders

def parse_parameters(textlines):
    general={}
    keys=[]
    for line in textlines:
        strings=line.split("=")
        if len(strings) > 1:
            key=strings[0].rstrip("0123456789")
            numberstrings=strings[1].split()
            try:
                numbers=[float(s) for s in numberstrings]
            except: 
                numbers=numberstrings
            
            if not( key in " ".join(keys) ) :
                general[key]=[]
                
            general[key].append(numbers)
            keys.append(key)
    
    for key in general.keys():
        if len(general[key])==1:
            general[key]=general[key][0]
        if len(general[key])==1:
            general[key]=general[key][0]
        else:
            general[key]=np.array(general[key])
    return general

def _parse(inputfile):
    sections, sectionheaders = split_sections(inputfile.readlines())
    gex={"header":sections["header"]}
    for header in sectionheaders:
        gex[header.strip("[").strip("]")]=parse_parameters(sections[header])
        print("header {} parsed".format(header))
    return gex

def parse(nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'r') as f:
            return _parse(f, **kw)
    else:
        return _parse(nameorfile, **kw)


