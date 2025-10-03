import yaml
import numpy as np
import pygrib
import h5py
import xarray as xr
import pyproj
import pickle

def LoadConfigFileFromYaml(yamlFile):
    with open(yamlFile, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    return data_loaded

def check_is_typelist(var):
    if (isinstance(var, int) | isinstance(var, str) | isinstance(var, dict)):
        return [var]
    elif isinstance(var, list):
        return var
    else:
        raise TypeError(f'wrong var dtype: {type(var)}')

def get_vars_from_nc(file_nc, vars, date = None):
    list_vars = check_is_typelist(vars)
    print(f'INFO:LoadWriteData:reading {file_nc}')
    with xr.open_dataset(file_nc) as nc_dataset:
        if date is None:
            try:
                date_get = nc_dataset.time.values[0]
            except IndexError:
                date_get = None
        else:
            date_get = date
        listArrays = []
        for var in list_vars:
            print(f'INFO:LoadWriteData:get {var} values')
            if ((var == 'lat') | (var == 'lon') | (var == 'latitude') | (var == 'longitude')):
                listArrays.append(nc_dataset[var].values.copy())
            elif var == 'flash_accumulation' and "time" not in nc_dataset.dims:  # flash data has not (t, y, x) dimensions and is rotated
                listArrays.append(np.flipud(nc_dataset[var].values))
            else:
                listArrays.append(nc_dataset[var].sel(time=date_get).values.copy())
        if len(list_vars) == 1:
            return listArrays[0]
        else:
            return listArrays

def get_lat_lon_from_nc(file_nc):
    try:
        lat, lon = get_vars_from_nc(file_nc, vars = ['lat', 'lon'])
    except KeyError:  # flash data is rotated
        lat_rot, lon_rot = get_vars_from_nc(file_nc, vars = ['latitude', 'longitude'])
        lat = np.flipud(lat_rot)
        lon = np.flipud(lon_rot)
    return lat.copy(), lon.copy()
        
def get_lat_lon_raw_from_msg(msg):
    try:
        lat, lon = msg.latlons()
    except ValueError:
        n_x = msg.Nx
        n_y = msg.Ny
        lat = msg.latitudes.reshape((n_y, n_x))
        lon = msg.longitudes.reshape((n_y, n_x))
    return lat.copy(), lon.copy()

def get_msg_from_code(grib_obj, code):
    if isinstance(code, int):
        grb = grib_obj.message(code)
    elif isinstance(code, str):
        try:
            grb = grib_obj.select(shortName = code)[0]
        except ValueError:
            name, lev = code.split('|')
            grb = grib_obj.select(shortName = name, level = int(lev))[0]
    elif isinstance(code, dict):
        grb = grib_obj.select(**code)[0]
    else:
        raise TypeError(f'wrong var dtype: {type(code)}')
    return grb

def get_vars_from_grib(file_grib, vars):
    list_vars = check_is_typelist(vars)
    grbs = pygrib.open(file_grib)
    print(f'INFO:LoadWriteData:reading {file_grib}')
    first_grb = grbs.select()[0]
    lat_raw, lon_raw = get_lat_lon_raw_from_msg(first_grb)
    if lat_raw[0, 0] > lat_raw[-1, 0]:
        lat_must_flip = True
        lat = np.flipud(lat_raw)
    else:
        lat_must_flip = False
        lat = lat_raw.copy()
    values_to_get = []
    for var in list_vars:
        if var == 'lat':
            print(f'INFO:LoadWriteData:get latitude grid')
            values_to_get.append(lat)
        elif var == 'lon':
            print(f'INFO:LoadWriteData:get longitude grid')
            values_to_get.append(np.where(lon_raw > 180., lon_raw - 360., lon_raw))
        else:
            grb = get_msg_from_code(grbs, var)
            try:
                print(f'INFO:LoadWriteData:get {grb.name} values in {grb.units} at {grb.level} ({grb.typeOfLevel})')
            except RuntimeError:
                print('INFO:LoadWriteData:get values')
            if lat_must_flip:
                values_to_get.append(np.flipud(grb["values"]))
            else:
                values_to_get.append(grb["values"])
    grbs.close()
    if len(list_vars) == 1:
        return values_to_get[0]
    else:
        return values_to_get

def get_lat_lon_from_grib(file_grib):
    lat, lon = get_vars_from_grib(file_grib, vars = ['lat', 'lon'])
    return lat.copy(), lon.copy()

def get_vars_from_HDF5(filename, vars):
    list_vars = check_is_typelist(vars)
    hf = h5py.File(filename, 'r')
    print(f'INFO:reading {filename}')
    list_values = []
    for path in list_vars:
        groups, var = path.split(':')[:-1], path.split(':')[-1]
        grp = hf.get(groups[0])
        for group in groups[1:]:
            grp = grp.get(group)
        print(f'INFO:get {var} values')
        values_raw = grp.get(var)[:].copy()
        values_flip = np.flip(
            np.where(values_raw == -8888000., 0.0, values_raw),
            axis=0
        )
        values = np.where(values_flip == -9999000., np.nan, values_flip)
        list_values.append(values)
    hf.close()
    if len(list_values) == 1:
        return list_values[0]
    else:
        return list_values

def get_lat_lon_from_HDF5(filename):
    hf = h5py.File(filename, 'r')
    print(f'INFO:reading {filename}')
    # get projection params
    where = hf.get('where')
    projection = pyproj.Proj(where.attrs.get('projdef').decode())
    ll_lat = where.attrs.get('LL_lat')
    ll_lon = where.attrs.get('LL_lon')
    ur_lat = where.attrs.get('UR_lat')
    ur_lon = where.attrs.get('UR_lon')
    res_x = where.attrs.get('xsize')
    res_y = where.attrs.get('ysize')
    hf.close()
    # transform lat-lon coordinates to meters
    ll_x, ll_y = projection(ll_lon, ll_lat)
    ur_x, ur_y = projection(ur_lon, ur_lat)
    # build grid in meters
    xi = np.linspace(int(np.round(ll_x, 0)), int(np.round(ur_x, 0)), res_x)
    yi = np.linspace(int(np.round(ll_y, 0)), int(np.round(ur_y, 0)), res_y)
    x, y = np.meshgrid(xi, yi)
    # reproject to lat-lon coordinates
    print(f'INFO:get lat-lon coordinates')
    lon2D, lat2D = projection(x, y, inverse=True)
    return lat2D.copy(), lon2D.copy()

def build_dataset(values, date, lat, lon, var_name, attrs_var = {}, attrs_nc = {}):
    attrs_var.update({'coordinates': 'time lat lon'})
    attrs_nc.update({'history': 'file created for spatial verification purposes'})
    ds = xr.Dataset(
        {var_name: xr.DataArray(
            values.reshape(1, values.shape[0], values.shape[1]), 
            dims = ['time', 'y', 'x'], 
            attrs = attrs_var
        )}, 
        coords = {
            'time': [date], 
            'lat': (('y', 'x'), lat, {"units": "degrees_north"}), 
            'lon': (('y', 'x'), lon, {"units": "degrees_north"}), 
        },
        attrs = attrs_nc
    )
    return ds.copy()

def LoadPickle(pickleFile):
    file = open(pickleFile, 'rb')
    data = pickle.load(file)
    file.close()
    return data

def SavePickle(var, filename):
    file = open(filename, 'wb')
    pickle.dump(var.copy(), file)
    file.close()
