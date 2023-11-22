#!/usr/bin/env python
# coding: utf-8

import os
import sys
sys.path.append('../libs/')
import numpy as np
import pandas as pd
import h5py
from datetime import datetime, timedelta
from LoadWriteData import LoadConfigFileFromYaml, CheckAndBuildGrid, BuildXarrayDataset

obs = 'IMERG_pcp'
type_product = 'B'

def make_dir_obs(obs, case):
    cwd = os.getcwd()
    os.chdir(f'../../OBSERVATIONS/')
    if os.path.exists(f'data_{obs}/') == False:
        os.mkdir(f'data_{obs}')
    os.chdir(f'data_{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
        print(f'INFO: ../../OBSERVATIONS/data_{obs}/{case}/ directory created')
    os.chdir(cwd)
    obs_path = f'../../OBSERVATIONS/data_{obs}/{case}/'
    return obs_path

def get_latlon2D_from_IMERG(hdf5File, latName = 'lat', lonName = 'lon'):
    obs_lat0, obs_lon0 = get_vars_from_IMERG(hdf5File, [latName, lonName])
    lat2D, lon2D = CheckAndBuildGrid(obs_lat0, obs_lon0)
    return lat2D.copy(), lon2D.copy()

def get_vars_from_IMERG(hdf5File, listVar, groupName = 'Grid'):
    print(f'INFO:reading {hdf5File}')
    hf = h5py.File(hdf5File, 'r')
    listArrays = []
    for var in listVar:
        values = hf.get(groupName).get(var)[:].copy()
        ndims = len(values.shape)
        print(f'INFO:get {var} values ({ndims}D var)')
        if ndims == 3:
            listArrays.append(np.transpose(values[0, :]))
        else:
            listArrays.append(values)
    hf.close()
    if len(listVar) == 1:
        return listArrays[0]
    else:
        return listArrays
    
def main(case, user, password):
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')
    
    # observation database info
    config_obs_db = LoadConfigFileFromYaml(f'../../config/obs_db/config_{obs_db}.yaml')
    obs_filename = config_obs_db['format']['filename']
    obs_var_get = config_obs_db['vars'][var_verif]['var']

    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'../../config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')

    obs_path = make_dir_obs(obs, case)
    
    dates = pd.date_range(date_ini, date_end, freq = '1H').to_pydatetime()
    files_to_remove = []
    for date in dates:
        # set date params
        day_of_year = date.timetuple().tm_yday
        date_0h = datetime(date.year, date.month, date.day)
        minutes_from_date_0h = int((date - date_0h).total_seconds() / 60.)
        # download 30-min files
        file_00min = f'3B-HHR-L.MS.MRG.3IMERG.{datetime.strftime(date, "%Y%m%d-S%H%M%S-E%H2959")}.{str(minutes_from_date_0h).zfill(4)}.V06{type_product}.HDF5'
        file_30min = f'3B-HHR-L.MS.MRG.3IMERG.{datetime.strftime(date + timedelta(minutes = 30), "%Y%m%d-S%H%M%S-E%H5959")}.{str(minutes_from_date_0h + 30).zfill(4)}.V06{type_product}.HDF5'
        print(f'INFO:downloading files: {[file_00min, file_30min]}')
        os.system(f'wget --no-check-certificate --user {user} --password {password} https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHL.06/{date.year}/{day_of_year}/{file_00min}')
        os.system(f'wget --no-check-certificate --user {user} --password {password} https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHL.06/{date.year}/{day_of_year}/{file_30min}')
        # postprocess raw files
        values_intrahour = []
        for file in (file_00min, file_30min):
            values_pcp_raw = get_vars_from_IMERG(file, [obs_var_get,])
            values_intrahour.append(values_pcp_raw.copy())
            if file == file_00min:
                lat2D, lon2D = get_latlon2D_from_IMERG(file)
            files_to_remove.append(file)

        date_process = date + timedelta(hours = 1)
        print(f'INFO:compute mean from {datetime.strftime(date, "%Y%m%d-%H:%M")} and {datetime.strftime(date + timedelta(minutes = 30), "%Y%m%d-%H:%M")} for accumulated pcp values at {datetime.strftime(date_process, "%Y%m%d-%H:%M")}')
        values_pcp_process = np.mean(values_intrahour, axis = 0)
        # save new files
        new_file = datetime.strftime(date_process, f'{obs_path}{obs_filename}')
        dataset = BuildXarrayDataset(values_pcp_process, lon2D, lat2D, date_process, varName = var_verif, descriptionNc = f'IMERG | 1-hour accumulated precipitation | {datetime.strftime(date, "%Y%m%d%H")}-{datetime.strftime(date_process, "%Y%m%d%H")}')
        dataset.to_netcdf(new_file, compute='True')

    # remove raw files
    for file in files_to_remove:
        print(f'INFO:removing {file}')
        os.remove(file)
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
