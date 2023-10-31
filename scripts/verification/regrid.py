#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append('scripts/libs/')
import numpy as np
import cartopy.crs as ccrs
from datetime import datetime, timedelta
from scipy.interpolate import griddata
from matplotlib import pyplot as plt
from LoadWriteData import LoadConfigFileFromYaml, BuildXarrayDataset
from dicts import get_grid_function, get_data_function, colormaps, postprocess_function
from plots import PlotMapInAxis

freqHours = 1 # ALL CODE IS DEVELOPED FOR DATA WITH 1 HOUR TIME RESOLUTION
old_inits = ['2020091506', '2020091512', '2020091518', '2020091606', '2020091612', '2020091618'] # TESTING!!!

def main(obs, case, exp):
    # OBS data: database + variable
    obsDB, varRaw = obs.split('_')

    # observation database info
    dataObs = LoadConfigFileFromYaml(f'config/config_{obsDB}.yaml')
    obsFileName = dataObs['format']['filename']
    obsFileFormat = dataObs['format']['extension']
    print(f'Load config file for {obsDB} database: \n file name: {obsFileName}; file format: {obsFileFormat}')

    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H')
    bounds = dataCase['location']['NOzoom']
    print(f'Load config file for {case} case study: \n init: {dataCase["dates"]["ini"]}; end: {dataCase["dates"]["end"]}')

    # exp data
    dataExp = LoadConfigFileFromYaml(f'config/config_{exp}.yaml')
    model = dataExp['model']['name']
    exp_filepaths = dataExp['format']['filepaths']
    exp_filename_dateformat = dataExp['format']['filename']
    exp_fileformat = dataExp['format']['extension']
    exp_var_get = dataExp['vars'][varRaw]['var']
    is_accum = dataExp['vars'][varRaw]['accum']
    postprocess = dataExp['vars'][varRaw]['postprocess']
    exp_var_description = dataExp['vars'][varRaw]['description']
    exp_var_units = dataExp['vars'][varRaw]['units']
    print(f'Load config file for {exp} simulation: \n model: {model}; file paths: {exp_filepaths}; file name: {exp_filename_dateformat}; file format: {exp_fileformat}; variable to extract: {exp_var_get} ({varRaw}: {exp_var_description}, in {exp_var_units})')
    
    # init times of nwp
    for init_time in dataExp['inits'].keys():
        # INIT OF TESTING!!!!
        if np.isin(init_time, old_inits).item() == True:
            exp_var_get = 315
        # END OF TESTING!!!
        date_exp_end = dataExp['inits'][init_time]['fcast_horiz']
        
        # set lead times from experiments
        date_simus_ini = datetime.strptime(init_time, '%Y%m%d%H')
        date_simus_end = datetime.strptime(date_exp_end, '%Y%m%d%H')
        if date_simus_ini < date_ini:
            forecast_ini = int((date_ini - date_simus_ini).total_seconds() / 3600.0)
        else:
            forecast_ini = 0
        forecast_horiz = int((date_simus_end - date_simus_ini).total_seconds() / 3600.0)
        if is_accum == True:
            forecast_ini += 1
            forecast_horiz += 1
        print(f'Forecast from {exp}: {init_time}+{str(forecast_ini).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_ini), "%Y%m%d%H")}) up to {init_time}+{str(forecast_horiz).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_horiz), "%Y%m%d%H")})')
        
        # link simus to SIMULATIONS/
        filesPath = exp_filepaths[dataExp['inits'][init_time]['path']].replace('%exp', exp)
        os.system(f'ln -s {datetime.strftime(date_simus_ini, filesPath)}{exp_filename_dateformat.replace("%Y", "*").replace("%m", "*").replace("%d", "*").replace("%H", "*").replace("%M", "*").replace("%LL", "*")} SIMULATIONS/{exp}/data_orig/{init_time}/') # TESTING!!!
        os.system(f'ls -ltr SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dateformat.replace("%Y", "*").replace("%m", "*").replace("%d", "*").replace("%H", "*").replace("%M", "*").replace("%LL", "*")}') # TESTING!!!

        # get lat, lon coordinates from observations and simus at, for example, initial lead time
        if is_accum == True:
            obs_file = datetime.strftime(date_ini + timedelta(hours = 1), f'OBSERVATIONS/data_{obs}/{case}/{obsFileName}')
        else:
            obs_file = datetime.strftime(date_ini, f'OBSERVATIONS/data_{obs}/{case}/{obsFileName}')
        simus_file = datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dateformat.replace("%LL", str(forecast_ini).zfill(2))}') # TESTING!!!
        obs_lat, obs_lon = get_grid_function[obsFileFormat](obs_file)
        simus_lat, simus_lon = get_grid_function[exp_fileformat](simus_file)
        print(f'Lat lon coordinates from {obsDB}: \n --- lat --- \n{obs_lat} \n --- lon --- \n{obs_lon}')
        print(f'Lat lon coordinates from {exp}: \n --- lat --- \n{simus_lat} \n --- lon --- \n{simus_lon}')

        for forecast in range(forecast_ini, forecast_horiz + 1, freqHours):
            # get original simus
            if is_accum == True:
                # example: pcp(t) = tp(t) - tp(t-1); where pcp is 1-hour accumulated precipitation and tp the total precipitation
                data_t = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dateformat.replace("%LLL", str(forecast).zfill(3))}'), [exp_var_get])
                data_dt = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dateformat.replace("%LLL", str(forecast - freqHours).zfill(3))}'), [exp_var_get])
                data = data_t - data_dt
            else:
                data = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dateformat.replace("%LL", str(forecast).zfill(2))}'), [exp_var_get]) # TESTING!!!
            
            # postprocessing??
            if postprocess != 'None':
                data_fp = postprocess_function[postprocess](data)
            else:
                data_fp = data.copy()

            # plot original simus
            fig = plt.figure(0, figsize=(9. / 2.54, 9. / 2.54), clear = True)
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            PlotMapInAxis(ax, data_fp, simus_lat, simus_lon, extent = bounds, titleLeft = f'{model} [{exp}] (orig)\n', titleRight = f'\nValid: {init_time}+{str(forecast).zfill(2)} UTC', cbLabel = f'{exp_var_description} ({exp_var_units})', yLeftLabel = False, yRightLabel = True, cmap = colormaps[varRaw]['map'], norm = colormaps[varRaw]['norm'])
            fig.savefig(f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{model}_{exp}_orig_{init_time}+{str(forecast).zfill(2)}_pcolormesh.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close(0)

            # regridding simus
            print(f'Regridding {init_time}+{str(forecast).zfill(2)} time step from {exp} (original grid)')
            regridded_data = griddata(
                (simus_lon.flatten(), simus_lat.flatten()),
                data_fp.flatten(),
                (obs_lon, obs_lat),
                method = 'linear'
            )

            # write netCDF
            ds = BuildXarrayDataset(regridded_data, obs_lon, obs_lat, date_simus_ini + timedelta(hours = forecast), varName = varRaw, lonName = 'lon', latName = 'lat', descriptionNc = f'{model} - {exp} | {exp_var_description} - {init_time}+{str(forecast).zfill(2)}')
            ds.to_netcdf(datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_regrid/{init_time}/{model}_{exp}_{varRaw}_{obsDB}grid_{init_time}+{str(forecast).zfill(2)}.nc'), compute='True')
            print('... DONE')
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
