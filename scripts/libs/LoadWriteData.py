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

def GetLatLon2DFromGrib(gribFile, latName = 'lat', lonName = 'lon'):
    lat, lon = GetVarsFromGrib(gribFile, [latName, lonName])
    lat2D, lon2D = CheckAndBuildGrid(lat, lon)
    return lat2D.copy(), lon2D.copy()
    
def GetVarsFromGrib(gribFile, listVar):
    print(f'INFO:LoadWriteData:reading {gribFile}')
    grbs = pygrib.open(gribFile)
    grb = grbs.select()[0]
    lats, lons = grb.latlons()
    listArrays = []
    for var in listVar:
        print(f'INFO:LoadWriteData:get {var} values')
        if var == 'lat':
            listArrays.append(lats.copy())
        elif var == 'lon':
            listArrays.append(lons.copy())
        else:
            if isinstance(var, int):
                grb = grbs.message(var)
            else:
                if len(var.split('|')) == 1:
                    grb = grbs.select(shortName=var)[0]
                elif len(var.split('|')) == 2:
                    name, lev = var.split('|')
                    grb = grbs.select(shortName=name, level=int(lev))[0]
                else:
                    raise ValueError()
                
            listArrays.append(grb.values.copy())
    grbs.close()
    if len(listVar) == 1:
        return listArrays[0]
    else:
        return listArrays

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
