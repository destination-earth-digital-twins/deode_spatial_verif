import yaml
import numpy as np
import xarray as xr
import pygrib
import h5py
import pickle

def LoadConfigFileFromYaml(yamlFile):
    with open(yamlFile, 'r') as stream:
        data_loaded = yaml.safe_load(stream)
    return data_loaded

def CheckAndBuildGrid(lat, lon):
    if len(lat.shape) != len(lon.shape):
        raise ValueError('Shape of lat lon arrays must be the same')
    if len(lat.shape) == 1:
        lon2D, lat2D = np.meshgrid(lon, lat)
    elif len(lat.shape) == 2:
        lon2D = lon.copy()
        lat2D = lat.copy()       
    else:
        raise ValueError(f'Shape of lat lon arrays not possible')
    return lat2D.copy(), lon2D.copy() 
    
def GetLatLon2DfromNetCDF(ncFile, latName = 'lat', lonName = 'lon'):
    lat, lon = GetVarsFromNetCDF(ncFile, [latName, lonName])
    lat2D, lon2D = CheckAndBuildGrid(lat, lon)
    return lat2D.copy(), lon2D.copy()

def GetVarsFromNetCDF(ncFile, listVar):
    print(f'INFO:LoadWriteData:reading {ncFile}')
    with xr.open_dataset(ncFile) as ncDataset:
        listArrays = []
        for var in listVar:
            print(f'INFO:LoadWriteData:get {var} values')
            listArrays.append(ncDataset[var].values.copy())
        if len(listVar) == 1:
            return listArrays[0]
        else:
            return listArrays

def get_lat_lon_raw_from_msg(msg):
    try:
        lat, lon = msg.latlons()
    except ValueError:
        lat = msg.latitudes.reshape(msg.values.shape)
        lon = msg.longitudes.reshape(msg.values.shape)
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
    else:
        raise ValueError(f'wrong var dtype: {type(code)}')
    return grb

def get_vars_from_grib(file_grib, list_vars = []):
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
            print(f'INFO:LoadWriteData:get {grb.name} values in {grb.units} at {grb.level} ({grb.typeOfLevel})')
            if lat_must_flip:
                values_to_get.append(np.flipud(grb.values))
            else:
                values_to_get.append(grb.values.copy())
    grbs.close()
    if len(list_vars) == 1:
        return values_to_get[0]
    else:
        return values_to_get

def get_lat_lon_from_grib(file_grib):
    lat, lon = get_vars_from_grib(file_grib, list_vars = ['lat', 'lon'])
    return lat.copy(), lon.copy()

def BuildXarrayDataset(data, lons, lats, times, varName = 'var', lonName = 'lon', latName = 'lat', timesName = 'time', descriptionNc = ''):
    if ((len(data.shape) == 2) & (len(lons.shape) == 2) & (len(lats.shape) == 2) & (len([times]) == 1)):
        ds = xr.Dataset(
            data_vars = {varName: (["lon_dim", "lat_dim"], data)},
            coords = {
                lonName: (["lon_dim", "lat_dim"], lons),
                latName: (["lon_dim", "lat_dim"], lats),
                timesName: (times)
            },
            attrs=dict(description = descriptionNc)
        )
        return ds
    else:
        raise ValueError('data, lons and lats arguments must be bidimensional arrays. len(times) must be 1')

def LoadPickle(pickleFile):
    file = open(pickleFile, 'rb')
    data = pickle.load(file)
    file.close()
    return data

def SavePickle(var, filename):
    file = open(f'{filename}.pkl', 'wb')
    pickle.dump(var.copy(), file)
    file.close()
