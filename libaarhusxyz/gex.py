"""
Created on Fri Oct 29 11:36:28 2021

@author: mp
"""
import warnings

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
    number_channels = np.array(["Channel" in key for key in gex.keys()]).sum()
    for channel in range(1, 1 + number_channels):
        channel_key = f"Channel{channel}"
        tx_mom = gex[channel_key].get('TransmitterMoment', None)
        assert tx_mom is not None, f"gex[{channel_key}]['TransmitterMoment'] does not exist in the Gexfile"
        turn_key = f"NumberOfTurns{tx_mom}"
        gex[channel_key]['ApproxDipoleMoment'] = gex["General"][turn_key] * gex["General"]["TxLoopArea"] * gex[channel_key]["TxApproximateCurrent"]
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
        f.write(('{0}\n'.format(line)).encode("utf-8"))

def dump(gex, nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'wb') as f:
            return _dump(gex, f, **kw)
    else:
        return _dump(gex, nameorfile, **kw)
    
_dump_function = dump

class GEX(object):
    def __init__(self, gex_dict, **kw):
        if not isinstance(gex_dict, dict):
            gex_dict = parse(gex_dict, **kw)
        self.gex_dict = gex_dict

    # FIXME: fill in the rest here
    # def __str__(self):
    #     stuff

    def dump(self, *arg, **kw):
        _dump_function(self.gex_dict, *arg, **kw)


    @property
    def number_channels(self):
        return np.array(["Channel" in key for key in self.gex_dict.keys()]).sum()

    def gate_times(self, channel=1):
        gex = self.gex_dict
        
        if 'int' in str(type(channel)):
            ch_key = f"Channel{channel}"
        elif 'str' in str(type(channel)):
            warnings.warn("Passing a string in to channel is deprecated and will be removed in a future release.\n"\
                          "Please change the function call to 'gate_times' to use only an integer",
                          DeprecationWarning, stacklevel=2)
            ch_key=channel
        
        moment_name = gex[ch_key].get("TransmitterMoment", "")
        
        if "GateTime" + moment_name in gex['General']:
            gate_time_array = gex['General']['GateTime' + moment_name]
        elif "GateTime" in gex['General']:
            gate_time_array = gex['General']['GateTime']
        else:
            assert False, f"Unable to find General.GateTime or General.GateTime{moment_name} in GEX"

        remove_gates_from = int(gex[ch_key].get('RemoveGatesFrom', 0))
        no_gates = int(gex[ch_key].get('NoGates', len(gate_time_array)))
            
        return gate_time_array[remove_gates_from:remove_gates_from+no_gates,:] + gex[ch_key].get('GateTimeShift', 0.0) + gex[ch_key].get('MeaTimeDelay', 0.0)

    @property
    def tx_orientation(self):
        looptype = self.gex_dict['General']['LoopType']
        # See the aarhusinv manual for looptype definitions:
        # https://hgg.au.dk/fileadmin/HGGfiles/Software/AarhusInv/AarhusInv_manual_8.pdf
        # pg 49. section 6.1 "line 2, first integer source type"
        if looptype == 72:
            tx_orient = 'z'
        else:
            warnings.warn(f"\n*********************************************************************************************\n"+\
                          f"*\n"+\
                          f"* Unknown loop-type {looptype}.\n"+\
                          f"*   Please see https://hgg.au.dk/fileadmin/HGGfiles/Software/AarhusInv/AarhusInv_manual_8.pdf\n"+\
                          f"*     pg 49. section 6.1 'Line 2, first integer source type'\n"+\
                          f"*\n"+\
                          f"* Assuming TX-orientation is 'Z'\n"+\
                          f"*\n"+\
                          f"*********************************************************************************************\n",
                          DeprecationWarning, stacklevel=2)
            tx_orient = 'z'
        return tx_orient

    def transmitter_waveform(self, channel: int = 1):
        tx_wf_key = f'Waveform{self.transmitter_moment(channel)}Point'
        return self.gex_dict['General'][tx_wf_key]

    def transmitter_moment(self, channel: int = 1):
        ch_key = f"Channel{channel}"
        return self.gex_dict[ch_key]['TransmitterMoment']

    def rx_orientation(self, channel: int = 1):
        ch_key = f"Channel{channel}"
        return self.gex_dict[ch_key]['ReceiverPolarizationXYZ']

    def uniform_data_std(self, channel: int = 1):
        ch_key = f"Channel{channel}"
        return self.gex_dict[ch_key]['UniformDataSTD']

    def no_gates(self, channel: int = 1):
        ch_key = f"Channel{channel}"
        return self.gex_dict[ch_key]['NoGates']

    def remove_initial_gates(self, channel: int = 1):
        ch_key = f"Channel{channel}"
        return self.gex_dict[ch_key]['RemoveInitialGates']


    def __getattr__(self, name):
        return self.gex_dict[name]

    def plot(self, ax=None):
        if ax is None:
            ax = plt.gca()

        waveform = [self.transmitter_waveform(channel) for channel in range(1, 1 + self.number_channels)]

        time_input_currents = [waveform[channel][:, 0]  for channel in range(self.number_channels)]
        input_currents = [waveform[channel][:, 1] for channel in range(self.number_channels)]

        colors = ['red', 'purple']
        for channel in range(1, 1 + self.number_channels):
            ax.vlines(self.gate_times(channel)[:, 0], 0, 0.5, color=colors[channel-1], label=f"Channel{channel} ({self.transmitter_moment(channel)}) gates")

        for channel in range(self.number_channels):
            ax.plot(time_input_currents[channel], input_currents[channel], label=self.transmitter_moment(channel + 1))

        ax.set_xlabel("Time")
        ax.set_ylabel("Current")
        ax.set_xscale("symlog", linthresh=1e-6)
        ax.legend(loc="upper left")
        plt.tight_layout()

    def __repr__(self):
        waveform = [self.transmitter_waveform(channel) for channel in range(1, 1 + self.number_channels)]
        input_times = [len(waveform[channel][:, 0]) for channel in range(self.number_channels)]
        gate_times = [len(self.gate_times(channel)[:, 0]) for channel in range(1, 1 + self.number_channels)]
        
        return "\n".join([
            (self.header or "[Unnamed system]"),
            "--------------------------------",
            "Channels: %s" % self.number_channels,
            "\n".join([
                "Channel: %s (%s)\n  Waveworm timepoints: %s\n  Gate times: %s (of which early: %s)" % (
                    channel,
                    self.transmitter_moment(channel + 1),
                    input_times[channel],
                    gate_times[channel],
                    (self.gate_times(channel + 1)[:, 0] < self.transmitter_waveform(channel + 1)[:, 0].max()).sum()
                )
                for channel in range(self.number_channels)]),
            ])
    
    def _ipython_display_(self):
        self.plot()
