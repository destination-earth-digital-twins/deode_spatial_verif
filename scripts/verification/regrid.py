#!/usr/bin/env python
# coding: utf-8

import re
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

def lead_time_replace(text, replace_with = '*'):
    pattern = r'(%LL+)'
    new_text = re.sub(pattern, lambda match: replace_function(match.group(0), replace_with), text)
    return new_text

def replace_function(text, replace_with):
    if isinstance(replace_with, int):
        return str(replace_with).zfill(len(text) - 1)
    else:
        return "*"

def main(obs, case, exp):
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')

    # observation database info
    config_obs_db = LoadConfigFileFromYaml(f'config/obs_db/config_{obs_db}.yaml')
    obs_filename = config_obs_db['format']['filename']
    obs_fileformat = config_obs_db['format']['fileformat']
    if config_obs_db['vars'][var_verif]['postprocess'] == True:
        obs_var_get = var_verif
    else:
        obs_var_get = config_obs_db['vars'][var_verif]['var_raw']
    var_verif_description = config_obs_db['vars'][var_verif]['description']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    print(f'Load config file for {obs_db} database: \n file name: {obs_filename}; file format: {obs_fileformat}; var. to get: {obs_var_get} ({var_verif_description}, in {var_verif_units})')

    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    case_domain = config_case['location']['NOzoom']
    print(f'Load config file for {case} case study: \n init: {config_case["dates"]["ini"]}; end: {config_case["dates"]["end"]}')

    # exp data
    config_exp = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_filepaths = config_exp['format']['filepaths']
    exp_filename = config_exp['format']['filename']
    exp_fileformat = config_exp['format']['fileformat']
    exp_var_get = config_exp['vars'][var_verif]['var']
    is_accum = config_exp['vars'][var_verif]['accum']
    postprocess = config_exp['vars'][var_verif]['postprocess']
    print(f'Load config file for {exp} simulation: \n model: {exp_model}; file paths: {exp_filepaths}; file name: {exp_filename}; file format: {exp_fileformat}; var. to get: {exp_var_get} ({var_verif})')
    
    # init times of nwp
    for init_time in config_exp['inits'].keys():
        date_exp_end = config_exp['inits'][init_time]['fcast_horiz']
        
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
        print(f'Lead times from {exp}: {init_time}+{str(forecast_ini).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_ini), "%Y%m%d%H")}) up to {init_time}+{str(forecast_horiz).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_horiz), "%Y%m%d%H")})')
        
        # link simus to SIMULATIONS/
        filesPath = exp_filepaths[config_exp['inits'][init_time]['path']].replace('%exp', exp)
        exp_filename_no_lead = lead_time_replace(exp_filename)
        os.system(f'ln -s {datetime.strftime(date_simus_ini, filesPath)}{exp_filename_no_lead.replace("%Y", "*").replace("%m", "*").replace("%d", "*").replace("%H", "*").replace("%M", "*")} SIMULATIONS/{exp}/data_orig/{init_time}/')
        os.system(f'ls -ltr SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_no_lead.replace("%Y", "*").replace("%m", "*").replace("%d", "*").replace("%H", "*").replace("%M", "*")}')

        # get lat, lon coordinates from observations and simus at, for example, initial lead time
        if is_accum == True:
            obs_file = datetime.strftime(date_ini + timedelta(hours = 1), f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
        else:
            obs_file = datetime.strftime(date_ini, f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
        exp_filename_t = lead_time_replace(exp_filename, forecast_ini)
        simus_file = datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}')
        obs_lat, obs_lon = get_grid_function[obs_fileformat](obs_file)
        simus_lat, simus_lon = get_grid_function[exp_fileformat](simus_file)
        print(f'Lat lon coordinates from {obs_db}: \n --- lat --- \n{obs_lat} \n --- lon --- \n{obs_lon}')
        print(f'Lat lon coordinates from {exp}: \n --- lat --- \n{simus_lat} \n --- lon --- \n{simus_lon}')

        for forecast in range(forecast_ini, forecast_horiz + 1, freqHours):
            # get original simus
            if is_accum == True:
                # example: pcp(t) = tp(t) - tp(t-1); where pcp is 1-hour accumulated precipitation and tp the total precipitation
                exp_filename_t = lead_time_replace(exp_filename, forecast)
                exp_filename_dt = lead_time_replace(exp_filename, forecast - freqHours)
                data_t = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}'), [exp_var_get])
                data_dt = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dt}'), [exp_var_get])
                data = data_t - data_dt
            else:
                exp_filename_t = lead_time_replace(exp_filename, forecast)
                data = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}'), [exp_var_get])
            
            # postprocessing??
            if postprocess != 'None':
                data_fp = postprocess_function[postprocess](data)
            else:
                data_fp = data.copy()

            # plot original simus
            fig = plt.figure(0, figsize=(9. / 2.54, 9. / 2.54), clear = True)
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            PlotMapInAxis(ax, data_fp, simus_lat, simus_lon, extent = case_domain, titleLeft = f'{exp_model} [{exp}] (orig)\n', titleRight = f'\nValid: {init_time}+{str(forecast).zfill(2)} UTC', cbLabel = f'{var_verif_description} ({var_verif_units})', yLeftLabel = False, yRightLabel = True, cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
            fig.savefig(f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{exp_model}_{exp}_orig_{init_time}+{str(forecast).zfill(2)}_pcolormesh.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
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
            ds = BuildXarrayDataset(regridded_data, obs_lon, obs_lat, date_simus_ini + timedelta(hours = forecast), varName = var_verif, lonName = 'lon', latName = 'lat', descriptionNc = f'{exp_model} - {exp} | {var_verif_description} - {init_time}+{str(forecast).zfill(2)}')
            ds.to_netcdf(datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_regrid/{init_time}/{exp_model}_{exp}_{var_verif}_{obs_db}grid_{init_time}+{str(forecast).zfill(2)}.nc'), compute='True')
            print('... DONE')
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
