import pandas as pd
import libaarhusxyz
import numpy as np

from scipy.interpolate import interp1d
from datetime import datetime

def _compute_xdist(fl):
    fl["prevdist"] = np.append(
        [0],
        np.sqrt(  (fl["x"].values[1:] - fl["x"].values[:-1])**2
                + (fl["y"].values[1:] - fl["y"].values[:-1])**2))
    fl.loc[np.append([False], fl["title"].values[1:] != fl["title"].values[:-1]), "prevdist"] = 0
    fl["xdist"] = fl.groupby(fl["title"])["prevdist"].cumsum()

def _compute_sounding_widths(fl):
    #compute appropriate start and end points along line in terms of xdistance 
    fl["next_title"] = fl["title"].shift(-1).fillna(-1)
    fl["prev_title"] = fl["title"].shift(1).fillna(-1)
    fl["next_xdist"] = fl["xdist"].shift(-1).fillna(fl.iloc[-1]["xdist"])
    fl["prev_xdist"] = fl["xdist"].shift(1).fillna(0)

    fl.loc[fl["title"] != fl["prev_title"], "prev_xdist"] = fl.loc[fl["title"] != fl["prev_title"], "xdist"]
    fl.loc[fl["title"] != fl["next_title"], "next_xdist"] = fl.loc[fl["title"] != fl["next_title"], "xdist"]

    fl.loc[fl["xdist"] - fl["prev_xdist"] > 50, "prev_xdist"] = fl.loc[fl["xdist"] - fl["prev_xdist"] > 50, "xdist"] - 50
    fl.loc[fl["next_xdist"] - fl["xdist"] > 50, "next_xdist"] = fl.loc[fl["next_xdist"] - fl["xdist"] > 50, "xdist"] + 50

    fl["left"] = (fl["prev_xdist"] + fl["xdist"]) / 2
    fl["right"] = (fl["xdist"] + fl["next_xdist"]) / 2

def _generate_cells(fl, df):
    #convert xdist along line to appropriate X, Y, and topo values 
    titles = fl['title'].unique()
    columns = ['x','y','topo']

    for ln in titles:
        mask_ln = fl.title == ln
        xdist = fl.loc[mask_ln, 'xdist'].values

        for col in columns:
            col_vals = fl.loc[mask_ln, col].values
            interp_func = interp1d(xdist, col_vals, fill_value=(col_vals[0],col_vals[-1]))
            fl.loc[mask_ln, col+'_left'] = interp_func(fl.loc[mask_ln, 'left'])
            fl.loc[mask_ln, col+'_right'] = interp_func(fl.loc[mask_ln, 'right'])

    cells = df.merge(fl, left_on='record', right_index=True)
    cells.loc[:,'z_bot_left'] = cells.topo_left-cells.dep_bot
    cells.loc[:,'z_bot_right'] = cells.topo_right-cells.dep_bot
    cells.loc[:,'z_top_left'] = cells.topo_left-cells.dep_top
    cells.loc[:,'z_top_right'] = cells.topo_right-cells.dep_top

    return cells
    
def _generate_points_array(cells):
    corner_vertices = pd.DataFrame(
        data={
        'x':['x_left','x_left','x_right','x_right'],
        'y':['y_left','y_left','y_right','y_right'],
        'z':['z_top_left','z_bot_left','z_bot_right','z_top_right']
    }, index = [0,1,2,3])

    cell_vertices = np.zeros((cells.shape[0],3,4))
    for n in range(4):
        cell_vertices[:,0,n] = cells.loc[:,  corner_vertices.loc[n,'x'] ] 
        cell_vertices[:,1,n] = cells.loc[:,  corner_vertices.loc[n,'y'] ] 
        cell_vertices[:,2,n] = cells.loc[:,  corner_vertices.loc[n,'z'] ]
    
    return np.swapaxes(cell_vertices,1,2).reshape((cells.shape[0]*4,3))

def _write_vtk(point_coordinates,
              cell_indices_np, cells_out_vtk, cell_types_out_vtk,
              cells,
              fid,
              attr_out):
    print('# vtk DataFile Version 2.0', file=fid)
    # print('AEM grid export of tin_id = %s on %s ' %(tri['meta']['tri_id'], datetime.now().isoformat()), file=fid)
    print('AEM grid export of TIN on %s ' %(datetime.now().isoformat(),), file=fid)
    print('ASCII', file=fid)

    fid.write('DATASET UNSTRUCTURED_GRID\n')

    print('POINTS', point_coordinates.shape[0], 'float', file=fid)
    np.savetxt(fid, point_coordinates, fmt='%.2f', delimiter=' ', newline='\n', )

    print('CELLS', cell_indices_np.shape[0], cells_out_vtk.size, file=fid)
    np.savetxt(fid, cells_out_vtk, fmt='%d', delimiter=' ', newline='\n')

    print('CELL_TYPES', cell_indices_np.shape[0], file=fid)
    np.savetxt(fid, cell_types_out_vtk, fmt='%d', delimiter=' ', newline='\n')

    print('CELL_DATA', cells.shape[0], file=fid)
    for attr in attr_out:
        if attr not in cells.columns.to_list():
            print(attr, ' is not in the given dataframe. this attribute will not be written to the VTK.')
            continue
        elif not np.issubdtype(cells.dtypes[attr],np.number):
            print(attr, ' is not a numeric column. this attribute will not be written to the VTK.')
            continue
        else:
            datatype = 'float'

            # if np.issubdtype(p.dtypes[attr],np.integer):
            #     datatype = 'long'
            attr_alphanumeric = "".join([ c if c.isalnum() else "_" for c in attr ])

            print('SCALARS', attr_alphanumeric, datatype,'1', file=fid)
            print('LOOKUP_TABLE default', file=fid)
            np.savetxt(fid, cells.loc[:, attr].to_numpy(), fmt='%f', delimiter=' ', newline='\n')

def _flatten_layer_data(model):
    df_list = []
    for key, val in model.layer_data.items():
        df_temp = model.layer_data[key].stack()
        df_temp.index.rename(('record','layer'), inplace=True)
        df_temp.rename(key, inplace=True)
        df_list.append(df_temp)
    return pd.concat(df_list, axis=1)

def _vtk_cell_data(points_array):
    indices_points = np.arange(points_array.size).reshape([-1,4])
    unique, unique_indices, unique_inverse = np.unique(np.around(points_array,3), True, True, axis=0)
    indices_points_unique = unique_inverse.reshape([-1,4])

    point_coordinates = unique

    cell_indices_np = indices_points_unique
    num_nodes = np.ones( (cell_indices_np.shape[0],1), dtype=int)*4

    cells_out_vtk = np.concatenate( (num_nodes,cell_indices_np),axis=1)
    cell_types_out_vtk = np.ones( (cell_indices_np.shape[0],1), dtype=int)*9 # 9 is for VTK_QUAD cell type

    return point_coordinates, cell_indices_np, cells_out_vtk, cell_types_out_vtk

def _dump(model, fid, attr_out = ['resistivity', 'resistivity_variance_factor','line_id','title', 'x', 'y',
                                  'topo','dep_top', 'dep_bot','tx_alt', 'invalt', 'invaltstd',
                                  'deltaalt', 'numdata', 'resdata',
                                  'restotal', 'doi_upper', 'doi_lower', 'xdist']):
    fl = model.flightlines

    df = _flatten_layer_data(model)

    _compute_xdist(fl)
    _compute_sounding_widths(fl)
    cells = _generate_cells(fl, df)
    points_array = _generate_points_array(cells)

    point_coordinates, cell_indices_np, cells_out_vtk, cell_types_out_vtk = _vtk_cell_data(points_array)

    _write_vtk(
        point_coordinates, cell_indices_np, cells_out_vtk, cell_types_out_vtk,
        cells,
        fid,
        attr_out)

def dump(model, nameorfile, **kw):
    if isinstance(nameorfile, str):
        with open(nameorfile, 'w') as f:
            return _dump(model, f, **kw)
    else:
        return _dump(model, nameorfile, **kw)
