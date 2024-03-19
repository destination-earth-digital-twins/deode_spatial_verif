#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('scripts/libs/')
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from LoadWriteData import LoadConfigFileFromYaml
from dicts import get_data_function, colormaps
from times import set_lead_times
from domains import set_domain_verif
from plots import PlotMapInAxis, PlotBoundsInAxis

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
        obs_var_get = config_obs_db['vars'][var_verif]['var']
    var_verif_description = config_obs_db['vars'][var_verif]['description']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    print(f'Load config file for {obs_db} database: \n file name: {obs_filename}; file format: {obs_fileformat}; variable to extract: {obs_var_get}')

    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    bounds_NOzoom = config_case['location']['NOzoom']
    verif_domains = config_case['verif_domain']
    print(f'Load config file for {case} case study: \n init: {config_case["dates"]["ini"]}; end: {config_case["dates"]["end"]}; domain: {bounds_NOzoom}; verification domains: {verif_domains}')

    # exp data
    config_exp = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']
    print(f'Load config file for {exp} regridded experiment: \n model: {exp_model}; variable to extract: {var_verif} ({var_verif_description}, in {var_verif_units})')

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
        print(f'Forecast from {exp}: {init_time}+{str(lead_times[0]).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_times[0].item()), "%Y%m%d%H")}) up to {init_time}+{str(lead_times[-1]).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_times[-1].item()), "%Y%m%d%H")})')

        # plot OBS vs Regrid exp at each timestep
        for lead_time in lead_times:
            obs_file = datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
            data_obs, lat_obs, lon_obs = get_data_function[obs_fileformat](obs_file, [obs_var_get, 'lat', 'lon'])

            file_nwp = f'SIMULATIONS/{exp}/data_regrid/{init_time}/{exp_model}_{exp}_{var_verif}_{obs_db}grid_{init_time}+{str(lead_time).zfill(2)}.nc'
            data_nwp, lat_nwp, lon_nwp = get_data_function['netCDF'](file_nwp, [var_verif, 'lat', 'lon'])

            # set verif domain
            verif_domain = set_domain_verif(date_simus_ini + timedelta(hours = lead_time.item()), verif_domains)
            if verif_domain is None:
                verif_domain = [lon_nwp[:, 0].max() + 0.5, lon_nwp[:, -1].min() - 0.5, lat_nwp[0, :].max() + 0.5, lat_nwp[-1, :].min() - 0.5]
                print(f'verif domain not established for {datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), "%Y%m%d%H")} UTC. By default: {verif_domain}')

            # plot large and small domain in different figs
            print(f'Plotting {obs_file} vs {file_nwp}')
            fig = plt.figure(0, figsize = (17.0 / 2.54, 9.0 / 2.54), dpi = 600, clear = True)

            ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
            PlotMapInAxis(ax1, data_obs, lat_obs, lon_obs, extent = bounds_NOzoom, titleLeft = f'{obs_db}\n', titleRight = datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), '\nValid: %Y%m%d%H UTC'), cbLabel = f'{var_verif_description} ({var_verif_units})', cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
            PlotBoundsInAxis(ax1, verif_domain, text = 'verif', color = 'black')

            ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
            PlotMapInAxis(ax2, data_nwp, lat_nwp, lon_nwp, extent = bounds_NOzoom, titleLeft = f'{exp_model} [{exp}] (regrid)\n', titleRight = f'\nValid: {init_time}+{str(lead_time).zfill(2)} UTC', cbLabel = f'{var_verif_description} ({var_verif_units})', yLeftLabel = False, yRightLabel = True, cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
            PlotBoundsInAxis(ax2, verif_domain, text = 'verif', color = 'black')

            fig.savefig(f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{exp_model}_{exp}_regrid_vs_{obs}_{init_time}+{str(lead_time).zfill(2)}_pcolormesh.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close(0)
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
