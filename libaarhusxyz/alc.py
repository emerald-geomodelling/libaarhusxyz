import pandas as pd
import re

def parse(nameorfile, xyz_columns=None):
    df = pd.read_csv(nameorfile, sep="= *", header=None).rename(columns={0:"canonical_name", 1:"position"})
    filt = df.canonical_name.isin(["Version", "System", "ChannelsNumber", "Dummy"])
    meta = df.loc[filt].set_index("canonical_name")["position"].to_dict()
    mapping = df.loc[~filt].astype({"position": int})

    if xyz_columns is not None:
        filt = mapping.position >= 0
        mapping["column"] = None
        mapping.loc[filt, "column"] = xyz_columns[mapping.loc[filt, "position"] - 1]
    
    return {"meta": meta,
            "mapping": mapping}

supported_fields = ["Date","Line","Magnetic","Misc1 ","Misc2","Misc3","Misc4","PowerLineMonitor","RxPitch","RxRoll","Time","Topography","TxAltitude","TxOffTime","TxOnTime","TxPeakTime","TxPitch","TxRoll","TxRxHoriSep","TxRxVertSep","UTMX","UTMY","Current_Ch01","Current_Ch02","Gate_Ch01.*","Gate_Ch02.*","STD_Ch01.*","STD_Ch02.*"]


def is_supported_field(fieldname):
    for pattern in supported_fields:
        m = re.match(pattern, fieldname)
        if m: return m
    return False

def _dump(xyz, f, columns=None):
    if columns is None:
        columns = xyz["file_meta"]["columns"]
    rows = [{"canonical_name": col, "position": idx + 1}
             for idx, col in enumerate(columns)
             if is_supported_field(col)]
    
    channels = set([row["canonical_name"][len("Gate_Ch"):].split("_")[0]
                    for row in rows
                    if row["canonical_name"].startswith("Gate_Ch")])

    header = [{"canonical_name": "Version", "position": 2},
              {"canonical_name": "System", "position": xyz.get("alc_info", {}).get("System", "Unknown")},
              {"canonical_name": "Dummy", "position": "*"},
              {"canonical_name": "ChannelsNumber", "position": len(channels)},
    ]
    
    rows = pd.DataFrame(header + rows)

    for idx, row in rows.iterrows():
        f.write('{0: <22}{1}\n'.format(row.canonical_name + "=", row.position))

def dump(xyz, nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'w') as f:
            return _dump(xyz, f, **kw)
    else:
        return _dump(xyz, nameorfile, **kw)
