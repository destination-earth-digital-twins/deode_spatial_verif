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
from times import set_lead_times, lead_time_replace
from domains import CropDomainsFromBounds
from dicts import get_grid_function, get_data_function, colormaps, postprocess_function
from plots import PlotMapInAxis

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
    bounds_W, bounds_E, bounds_S, bounds_N = case_domain
    print(f'Load config file for {case} case study: \n init: {config_case["dates"]["ini"]}; end: {config_case["dates"]["end"]}')

    # exp data
    config_exp = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
    exp_filepaths = config_exp['format']['filepaths']
    exp_filename = config_exp['format']['filename']
    exp_fileformat = config_exp['format']['fileformat']
    exp_var_get = config_exp['vars'][var_verif]['var']
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']
    postprocess = config_exp['vars'][var_verif]['postprocess']
    print(f'Load config file for {exp} simulation: \n model: {exp_model}; file paths: {exp_filepaths}; file name: {exp_filename}; file format: {exp_fileformat}; var. to get: {exp_var_get} ({var_verif})')
    
    # init times of nwp
    for init_time in config_exp['inits'].keys():
        date_exp_end = config_exp['inits'][init_time]['fcast_horiz']
        
        # set lead times from experiments
        date_simus_ini = datetime.strptime(init_time, '%Y%m%d%H')
        date_simus_end = datetime.strptime(date_exp_end, '%Y%m%d%H')
        lead_times = set_lead_times(date_ini, date_end, date_simus_ini, date_simus_end)
        if is_accum == True:
            lead_times = lead_times[lead_times >= 1].copy() # TODO: accum_hours instead 1h
        elif verif_at_0h == False:
            lead_times = lead_times[lead_times > 0].copy()
        else:
            pass
        print(f'Lead times from {exp}: {init_time}+{str(lead_times[0]).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_times[0].item()), "%Y%m%d%H")}) up to {init_time}+{str(lead_times[-1].item()).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_times[-1].item()), "%Y%m%d%H")})')
        
        # link simus to SIMULATIONS/
        filesPath = exp_filepaths[config_exp['inits'][init_time]['path']].replace('%exp', exp)
        exp_filename_no_lead = lead_time_replace(exp_filename)
        os.system(f'ln -s {datetime.strftime(date_simus_ini, filesPath)}{exp_filename_no_lead.replace("%Y", "*").replace("%m", "*").replace("%d", "*").replace("%H", "*").replace("%M", "*")} SIMULATIONS/{exp}/data_orig/{init_time}/')
        os.system(f'ls -ltr SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_no_lead.replace("%Y", "*").replace("%m", "*").replace("%d", "*").replace("%H", "*").replace("%M", "*")}')

        # get lat, lon coordinates from observations and simus at, for example, initial lead time
        obs_file = datetime.strftime(date_ini, f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
        exp_filename_t = lead_time_replace(exp_filename, lead_times[0].item())
        simus_file = datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}')
        obs_lat_orig, obs_lon_orig = get_grid_function[obs_fileformat](obs_file)
        simus_lat_orig, simus_lon_orig = get_grid_function[exp_fileformat](simus_file)
        
        # crop data to avoid ram issues
        obs_lat = CropDomainsFromBounds(obs_lat_orig, obs_lat_orig, obs_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
        obs_lon = CropDomainsFromBounds(obs_lon_orig, obs_lat_orig, obs_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
        simus_lat = CropDomainsFromBounds(simus_lat_orig, simus_lat_orig, simus_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
        simus_lon = CropDomainsFromBounds(simus_lon_orig, simus_lat_orig, simus_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
        print(f'Lat lon coordinates from {obs_db}: \n --- lat --- \n{obs_lat} \n --- lon --- \n{obs_lon}')
        print(f'Lat lon coordinates from {exp}: \n --- lat --- \n{simus_lat} \n --- lon --- \n{simus_lon}')

        for lead_time in lead_times:
            # get original simus
            exp_filename_t = lead_time_replace(exp_filename, lead_time.item())
            if is_accum == True:
                # example: pcp(t) = tp(t) - tp(t-1); where pcp is 1-hour accumulated precipitation and tp the total precipitation
                exp_filename_dt = lead_time_replace(exp_filename, lead_time.item() - 1) # TODO: accum_hours instead 1h
                data_t = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}'), exp_var_get)
                data_dt = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_dt}'), exp_var_get)
                if isinstance(exp_var_get, list): # assume all variables have accumulated values
                    data = []
                    for values_t, values_dt in zip(data_t, data_dt):
                        diff = values_t - values_dt
                        data.append(np.where(diff < 0, 0., diff))
                else:
                    diff = data_t - data_dt
                    data = np.where(diff < 0, 0., diff)
            else:
                data = get_data_function[exp_fileformat](datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}'), exp_var_get)
            
            # postprocessing?? and crop
            if postprocess != 'None':
                data_raw_domain = postprocess_function[postprocess](data)
                data_fp = CropDomainsFromBounds(data_raw_domain, simus_lat_orig, simus_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
            else:
                data_fp = CropDomainsFromBounds(data, simus_lat_orig, simus_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])

            # plot original simus
            valid_time = date_simus_ini + timedelta(hours = lead_time.item())
            fig = plt.figure(0, figsize=(11. / 2.54, 11. / 2.54), clear = True)
            ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            ax, cbar = PlotMapInAxis(
                ax = ax, 
                data = data_fp, 
                lat = simus_lat, 
                lon = simus_lon, 
                extent = case_domain, 
                title = f'{exp_model} [exp: {exp}] (orig grid)\nRun: {init_time} UTC\nValid on {valid_time.strftime("%Y-%m-%d at %Hz")} (+{str(lead_time).zfill(2)})', 
                cb_label = f'{var_verif_description} ({var_verif_units})', 
                left_grid_label = False, 
                right_grid_label = True, 
                cmap = colormaps[var_verif]['map'], 
                norm = colormaps[var_verif]['norm']
            )
            fig.savefig(f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{exp_model_in_filename}_{exp}_orig_{init_time}+{str(lead_time).zfill(2)}_pcolormesh.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close(0)

            # regridding simus
            print(f'Regridding {init_time}+{str(lead_time).zfill(2)} time step from {exp} (original grid)')
            regridded_data = griddata(
                (simus_lon.flatten(), simus_lat.flatten()),
                data_fp.flatten(),
                (obs_lon, obs_lat),
                method = 'linear'
            )

            # write netCDF
            ds = BuildXarrayDataset(regridded_data, obs_lon, obs_lat, date_simus_ini + timedelta(hours = lead_time.item()), varName = var_verif, lonName = 'lon', latName = 'lat', descriptionNc = f'{exp_model} - {exp} | {var_verif_description} - {init_time}+{str(lead_time).zfill(2)}')
            ds.to_netcdf(datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_regrid/{init_time}/{exp_model_in_filename}_{exp}_{var_verif}_{obs_db}grid_{init_time}+{str(lead_time).zfill(2)}.nc'), compute='True')
            print('... DONE')
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
