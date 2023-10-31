#!/usr/bin/env python
# coding: utf-8

import os
import sys
sys.path.append('../libs/')
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from LoadWriteData import LoadConfigFileFromYaml, CheckAndBuildGrid, BuildXarrayDataset

obs = 'IMERG_pcp'
typeStr = 'B'
#user = 'jgonzaleza'
#password = '3TDYjbKqWnzxWKe'

def get_latlon2D_from_IMERG(hdf5File, latName = 'lat', lonName = 'lon'):
    obs_lat0, obs_lon0 = get_vars_from_IMERG(hdf5File, [latName, lonName])
    lat2D, lon2D = CheckAndBuildGrid(obs_lat0, obs_lon0)
    return lat2D.copy(), lon2D.copy()

def get_vars_from_IMERG(hdf5File, listVar, groupName = 'Grid'):
    hf = h5py.File(hdf5File, 'r')
    listArrays = []
    for var in listVar:
        values = hf.get(groupName).get(var)[:].copy()
        ndims = len(values.shape)
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
    obsDB, var = obs.split('_')
    
    # observation database info
    dataObs = LoadConfigFileFromYaml(f'../../config/config_{obsDB}.yaml')
    obsFileName = dataObs['format']['filename']
    varGet = dataObs['vars'][var]['var']

    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'../../config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H')
    
    dates = pd.date_range(date_ini, date_end, freq = '1H').to_pydatetime()
    filesToRemove = []
    for date in dates:
        # set date params
        dayOfYear = date.timetuple().tm_yday
        date0h = datetime(date.year, date.month, date.day)
        minFrom0h = int((date - date0h).total_seconds() / 60.)
        # download 30-min files
        file1 = f'3B-HHR-L.MS.MRG.3IMERG.{datetime.strftime(date, "%Y%m%d-S%H%M%S-E%H2959")}.{str(minFrom0h).zfill(4)}.V06{typeStr}.HDF5'
        file2 = f'3B-HHR-L.MS.MRG.3IMERG.{datetime.strftime(date + timedelta(minutes = 30), "%Y%m%d-S%H%M%S-E%H5959")}.{str(minFrom0h + 30).zfill(4)}.V06{typeStr}.HDF5'
        print(f'downloading files: {[file1, file2]}')
        os.system(f'wget --no-check-certificate --user {user} --password {password} https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHL.06/{date.year}/{dayOfYear}/{file1}')
        os.system(f'wget --no-check-certificate --user {user} --password {password} https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGHHL.06/{date.year}/{dayOfYear}/{file2}')
        # postprocess raw files
        #listValues = []
        for file in (file1, file2):
            '''
            dataPcpRaw = get_vars_from_IMERG(file1, [varGet])
            listValues.append(dataPcpRaw.copy())
            if file == file1:
                lat2D, lon2D = get_latlon2D_from_IMERG(file2)
            '''
            filesToRemove.append(file)
        '''
        datePostProcess = date + timedelta(hours = 1)
        dataPcp = np.mean(listValues, axis = 0)
        # save new files
        filePostProcess = datetime.strftime(datePostProcess, f'{obsFileName}')
        print(f'save generated file {filePostProcess} at current directory')
        dataset = BuildXarrayDataset(dataPcp, lon2D, lat2D, datePostProcess, varName = var, descriptionNc = f'IMERG | 1-hour accumulated precipitation | {datetime.strftime(date, "%Y%m%d%H")}-{datetime.strftime(datePostProcess, "%Y%m%d%H")}')
        dataset.to_netcdf(filePostProcess, compute='True')
        # try to move to OBSERVATIONS folder
        codeReturn = os.system(f'mv {filePostProcess} ../../OBSERVATIONS/data_{obs}/{case}/')
        if codeReturn != 0:
            print('run set_environment.py first to create the adecuate paths and move observations to them')
        else:
            print(f'file {filePostProcess} moved to OBSERVATIONS/data_{obs}/{case}/')
        '''
    # remove raw files
    for file in filesToRemove:
        #os.remove(file)
        os.system(f'mv {file} ../../../databases/{obsDB}/')
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
