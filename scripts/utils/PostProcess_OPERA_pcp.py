import sys
sys.path.append('../libs/')
import h5py
import pyproj
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from LoadWriteData import LoadConfigFileFromYaml, BuildXarrayDataset

obs = 'OPERA_pcp'
obsFilenameRaw = 'ODC.LAM_%Y%m%d%H%M_000100.h5'

def get_vars_from_OPERA(filename, list_vars):
    # list_var must be a list with the "path" of the var join by ':' character
    hf = h5py.File(filename, 'r')
    list_values = []
    for path in list_vars:
        groups, var = path.split(':')[:-1], path.split(':')[-1]
        grp = hf.get(groups[0])
        for group in groups[1:]:
            grp = grp.get(group)
        list_values.append(grp.get(var)[:].copy())
    hf.close()
    if len(list_values) == 1:
        return list_values[0]
    else:
        return list_values

def get_latlon2D_from_OPERA(filename):
    hf = h5py.File(filename, 'r')
    # get projection params
    where = hf.get('where')
    projection = pyproj.Proj(where.attrs.get('projdef').decode())
    ll_lat = where.attrs.get('LL_lat')
    ll_lon = where.attrs.get('LL_lon')
    ur_lat = where.attrs.get('UR_lat')
    ur_lon = where.attrs.get('UR_lon')
    # transform lat-lon coordinates to meters
    ll_x, ll_y = projection(ll_lon, ll_lat)
    ur_x, ur_y = projection(ur_lon, ur_lat)
    # build grid in meters
    xi = np.linspace(int(np.round(ll_x, 0)), int(np.round(ur_x, 0)), where.attrs.get('xsize'))
    yi = np.linspace(int(np.round(ll_y, 0)), int(np.round(ur_y, 0)), where.attrs.get('ysize'))
    x, y = np.meshgrid(xi, yi)
    # reproject to lat-lon coordinates
    lon2D, lat2D = projection(x, y, inverse = True)
    hf.close()
    return lat2D.copy(), lon2D.copy()

def main(path_OPERA_raw, case):
    # OBS data: database + variable
    obsDB, var = obs.split('_')
    
    # observation database info
    dataObs = LoadConfigFileFromYaml(f'../../config/config_{obsDB}.yaml')
    obsFileName = dataObs['format']['filename']
    varGet = dataObs['vars'][var]['var']

    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'../../config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H') + timedelta(hours = 1)
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H') + timedelta(hours = 1)
    
    dates = pd.date_range(date_ini, date_end, freq = '1H').to_pydatetime()
    for date in dates:
        file_obs = datetime.strftime(date, f'{path_OPERA_raw}{obsFilenameRaw}')
        values = get_vars_from_OPERA(file_obs, [varGet,])
        lat_obs, lon_obs = get_latlon2D_from_OPERA(file_obs)
        ds = BuildXarrayDataset(np.flip(values, axis = 0), lon_obs, lat_obs, date, varName = var, lonName = 'lon', latName = 'lat', descriptionNc = f'OPERA | 1-hour accumulated precipitation | {datetime.strftime(date - timedelta(hours = 1), "%Y%m%d%H")}-{datetime.strftime(date, "%Y%m%d%H")}')
        ds.to_netcdf(datetime.strftime(date, f'../../OBSERVATIONS/data_{obs}/{case}/{obsFileName}'), compute='True')
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]))