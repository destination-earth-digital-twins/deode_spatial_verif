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
    ncDataset = xr.open_dataset(ncFile)
    listArrays = []
    for var in listVar:
        listArrays.append(ncDataset[var].values.copy())
    ncDataset.close()
    if len(listVar) == 1:
        return listArrays[0]
    else:
        return listArrays

def GetLatLon2DFromGrib(gribFile, latName = 'lat', lonName = 'lon'):
    lat, lon = GetVarsFromGrib(gribFile, [latName, lonName])
    lat2D, lon2D = CheckAndBuildGrid(lat, lon)
    return lat2D.copy(), lon2D.copy()
    
def GetVarsFromGrib(gribFile, listVar):
    grbs = pygrib.open(gribFile)
    grb = grbs.select()[0]
    lats, lons = grb.latlons()
    listArrays = []
    for var in listVar:
        if var == 'lat':
            listArrays.append(lats.copy())
        elif var == 'lon':
            listArrays.append(lons.copy())
        else:
            #msg = GetMsgFromNameVar(gribFile, var)
            msg = var
            grb = grbs.message(msg)
            listArrays.append(grb.values.copy())
    grbs.close()
    if len(listVar) == 1:
        return listArrays[0]
    else:
        return listArrays
'''
def GetMsgFromNameVar(filename, var):
    #level_type = ['hybrid', 'heightAboveGround', 'isobaricInhPa', 'entireAtmosphere']
    var_level_type = dict([('tp', 'heightAboveGround'), ('refl', 'heightAboveGround')])
    
    #var = 'refl'
    level_value = '1000'
    
    #for fc in range(1,2):
    #filename = '/home/sp4h/SCRATCH/hm_home/{}/archive/{}/fc{}+{:0>3}grib2_fp'.format(exp, run_1, run_2, fc)

    # Command to list GRIB2 file contents
    grib_ls_command = "grib_ls {}".format(filename)

    # Command to filter 'refl', 'heightAboveGround', and '300'
    grep_commands = [
        "grep -n '{}'".format(var),
        "grep '{}'".format(var_level_type[var]),
        "grep '{}'".format(level_value)
    ]

    # Combione all commands into a single string using the pipe symbol '|'
    combined_command = f"{grib_ls_command} | {' | '.join(grep_commands)}"

    try:
        # Execute the combined command and capture the output
        output = subprocess.check_output(combined_command, shell = True, text = True)

        # Print the output
        print(output)
    except subprocess.CalledProcessError as e:
        print(f"Error executing the command: {e}")

    message_number = int(output[0:3]) - 2
    return message_number
'''
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
