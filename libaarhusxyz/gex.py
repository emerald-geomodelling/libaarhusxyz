"""
Created on Fri Oct 29 11:36:28 2021

@author: mp
"""


import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt



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
    section={}
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
                section[key]=[]
                
            section[key].append(numbers)
            keys.append(key)
    
    for key in section.keys():
        if len(section[key])==1:
            section[key]=section[key][0]
        if len(section[key])==1:
            section[key]=section[key][0]
        else:
            section[key]=np.array(section[key])
    return section

def _parse(inputfile):
    sections, sectionheaders = split_sections(inputfile.readlines())
    gex={"header":sections["header"]}
    for header in sectionheaders:
        gex[header.strip("[").strip("]")]=parse_parameters(sections[header])
        print("header {} parsed".format(header))
    
    for channel in ["Channel1", "Channel2"]:
        if channel in gex.keys():
            if "Channel1" in channel:
                NumberOfTurns=gex["General"]["NumberOfTurnsLM"]
            elif "Channel2" in channel:
                NumberOfTurns=gex["General"]["NumberOfTurnsHM"]
            gex[channel]['ApproxDipoleMoment']= gex["General"]["NumberOfTurnsHM"] * gex["General"]["TxLoopArea"] * gex[channel]["TxApproximateCurrent"]
    return gex

def parse(nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'r') as f:
            return _parse(f, **kw)
    else:
        return _parse(nameorfile, **kw)

def _dump(gex, f, columns=None):
    lines=[]
    
    now = datetime.now() 
    gex['header']='/{0} gex file modified by the EmeraldProcessing toolbox '.format(now.strftime('%Y-%m-%d'))
    lines.append(gex['header'])
    
    gex_keys=(list(gex.keys()))
    gex_keys.remove('header')
    
    for key1 in gex_keys:
        #for key1 in ['General']:
        lines.append('\n[{}]'.format(key1))
        for key2 in gex[key1].keys():
            if 'General' in key1:
                lines.append('\n')
            a=gex[key1][key2]
            # the follwoing is a mess because the required format is depending on the paramter 
            if type(a) is np.ndarray:
                if type(a[0]) is np.str_:
                    lines.append('{0}={1}'.format(key2, ' '.join(['{}'.format(item) for item in a[:] ]))) 
                elif a.ndim==1:
                    digits=1
                    if 'TiBLowPassFilter' in key2:
                        lines.append('{0}=\t {1}'.format(key2, '\t'.join(['{:.2f}'.format(item) for item in a[:] ])) )
                    elif 'Position' in key2:
                        lines.append('{0}{1}=\t {2}'.format(key2, 1, '\t'.join(['{:.2f}'.format(item) for item in a[:] ])) )
                    else:
                        lines.append('{0}{1}=\t {2}'.format(key2, 1,'\t'.join(['{:f}'.format(item) for item in a[:] ])) )
                elif a.ndim==2:
                    digits=int(np.ceil(np.log10(a.shape[0])))
                    for n,row in enumerate(a):
                        if ('Waveform' in key2)  or ('GateTime' in key2):
                            lines.append(('{0}{1:0'+str(digits)+'d}=\t{2}').format(key2, n+1, '\t'.join(['{:e}'.format(item) for item in row ])) )
                        elif 'Position' in key2:
                            lines.append(('{0}{1:0'+str(digits)+'d}=\t{2}').format(key2, n+1, '\t'.join(['{:.2f}'.format(item) for item in row ])) )
                        else:
                            lines.append(('{0}{1:0'+str(digits)+'d}=\t{2}').format(key2, n+1, '\t'.join(['{}'.format(item) for item in row ])) )
            elif type(a) is float:
                if key2 in ['GateNoForPowerLineMonitor', 'RemoveInitialGates', 'NumberOfTurnsLM', 
                            'NumberOfTurnsHM','LoopType' , 'RxCoilNumber', 'NoGates', 'RemoveInitialGates',
                            'SystemResponseConvolution']:
                    lines.append('{0}={1}'.format(key2, int(a)))
                else:
                    lines.append('{0}={1}'.format(key2, a))
            elif type(a) is int:
                lines.append('{0}={1}'.format(key2, int(a)))
            elif type(a) is str:
                lines.append('{0}={1}'.format(key2, a))
    
    for line in lines:
        f.write('{0}\n'.format(line))

def dump(gex, nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'w') as f:
            return _dump(gex, f, **kw)
    else:
        return _dump(gex, nameorfile, **kw)
    
_dump_function = dump

class GEX(object):
    def __init__(self, gex_dict, **kw):
        if not isinstance(gex_dict, dict):
            gex_dict = parse(gex_dict, **kw)
        self.gex_dict = gex_dict

    def dump(self, *arg, **kw):
        _dump_function(self.gex_dict, *arg, **kw)

    def gate_times(self, channel='Channel1'):
        gex = self.gex_dict
        no_gates = int(gex[channel]['NoGates'])
        remove_gates_from = int(gex[channel].get('RemoveGatesFrom', 0))
        return gex['General']['GateTime'][remove_gates_from:no_gates,:] + gex[channel]['GateTimeShift'] + gex[channel].get('MeaTimeDelay', 0.0)

    def __getattr__(self, name):
        return self.gex_dict[name]

    def plot(self, ax=None):
        if ax is None:
            ax = plt.gca()
        
        waveform_hm = self.General['WaveformHMPoint']
        waveform_lm = self.General['WaveformLMPoint']

        time_input_currents_hm = waveform_hm[:,0]
        input_currents_hm = waveform_hm[:,1]
        time_input_currents_lm = waveform_lm[:,0]
        input_currents_lm = waveform_lm[:,1]

        ax.vlines(self.gate_times('Channel1')[:,0], 0, 0.5, color="red", label="LM gates")
        ax.vlines(self.gate_times('Channel2')[:,0], 0.5, 1, color="purple", label="HM gates")

        ax.plot(time_input_currents_hm, input_currents_hm, label="HM")
        ax.plot(time_input_currents_lm, input_currents_lm, label="LM")

        ax.set_xlabel("Time")
        ax.set_ylabel("Current")
        ax.set_xscale("symlog", linthresh=1e-6)
        ax.legend(loc="upper left")
        
