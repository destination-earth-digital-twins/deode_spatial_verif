#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('scripts/libs/')
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from LoadWriteData import LoadConfigFileFromYaml
from dicts import get_grid_function, get_data_function, colormaps, postprocess_function
from plots import PlotMapInAxis, PlotBoundsInAxis

freqHours = 1 # ALL CODE IS DEVELOPED FOR DATA WITH 1 HOUR TIME RESOLUTION

def main(obs, case, exp):
    # OBS data: database + variable
    obsDB, varRaw = obs.split('_')

    # observation database info
    dataObs = LoadConfigFileFromYaml(f'config/config_{obsDB}.yaml')
    obsFileName = dataObs['format']['filename']
    obsFileFormat = dataObs['format']['extension']
    if dataObs['vars'][varRaw]['postprocess'] == True:
        obsVar = varRaw
    else:
        obsVar = dataObs['vars'][varRaw]['var']
    print(f'Load config file for {obsDB} database: \n file name: {obsFileName}; file format: {obsFileFormat}; variable to extract: {obsVar}')

    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H')
    bounds_NOzoom = dataCase['location']['NOzoom']
    bounds_zoom = dataCase['location']['zoom']
    print(f'Load config file for {case} case study: \n init: {dataCase["dates"]["ini"]}; end: {dataCase["dates"]["end"]}; domain: {bounds_NOzoom}; domain (zoom): {bounds_zoom}')

    # exp data
    dataExp = LoadConfigFileFromYaml(f'config/config_{exp}.yaml')
    model = dataExp['model']['name']
    exp_var_description = dataExp['vars'][varRaw]['description']
    exp_var_units = dataExp['vars'][varRaw]['units']
    print(f'Load config file for {exp} regridded experiment: \n model: {model}; variable to extract: {varRaw} ({exp_var_description}, in {exp_var_units})')

    # init times of nwp
    for init_time in dataExp['inits'].keys():
        verif_domain_ini = None
        date_exp_end = dataExp['inits'][init_time]['fcast_horiz']

        # set lead times from experiments
        date_simus_ini = datetime.strptime(init_time, '%Y%m%d%H')
        date_simus_end = datetime.strptime(date_exp_end, '%Y%m%d%H')
        if date_simus_ini < date_ini:
            forecast_ini = int((date_ini - date_simus_ini).total_seconds() / 3600.0)
        else:
            forecast_ini = 0
        forecast_horiz = int((date_simus_end - date_simus_ini).total_seconds() / 3600.0)
        if dataExp['vars'][varRaw]['accum'] == True:
            forecast_ini += 1
            forecast_horiz += 1
        print(f'Forecast from {exp}: {init_time}+{str(forecast_ini).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_ini), "%Y%m%d%H")}) up to {init_time}+{str(forecast_horiz).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_horiz), "%Y%m%d%H")})')

        # plot OBS vs Regrid exp at each timestep
        for forecast in range(forecast_ini, forecast_horiz + 1, freqHours):
            obs_file = datetime.strftime(date_simus_ini + timedelta(hours = forecast), f'OBSERVATIONS/data_{obs}/{case}/{obsFileName}')
            data_obs = get_data_function[obsFileFormat](obs_file, [obsVar])
            lat_obs, lon_obs = get_grid_function[obsFileFormat](obs_file)

            file_nwp = f'SIMULATIONS/{exp}/data_regrid/{init_time}/{model}_{exp}_{varRaw}_{obsDB}grid_{init_time}+{str(forecast).zfill(2)}.nc'
            data_nwp = get_data_function['netCDF'](file_nwp, [varRaw])
            lat_nwp, lon_nwp = get_grid_function['netCDF'](file_nwp)

            # set verif domain
            try:
                if dataExp['vars'][varRaw]['accum'] == True:
                    verif_domain = dataCase['verif_domain'][datetime.strftime(date_simus_ini + timedelta(hours = forecast - 1), '%Y%m%d%H')] # namefiles from accum vars have a delay respect verif_domain timesteps from dataCase
                else:
                    verif_domain = dataCase['verif_domain'][datetime.strftime(date_simus_ini + timedelta(hours = forecast), '%Y%m%d%H')]
                verif_domain_ini = verif_domain
            except KeyError:
                if verif_domain_ini is not None:
                    verif_domain = verif_domain_ini
                else:
                    verif_domain = [lon_nwp[:, 0].max() + 0.5, lon_nwp[:, -1].min() - 0.5, lat_nwp[0, :].max() + 0.5, lat_nwp[-1, :].min() - 0.5]
                    print(f'verif domain not established for {datetime.strftime(date_simus_ini + timedelta(hours = forecast), "%Y%m%d%H")} UTC. By default: {verif_domain}')

            # plot large and small domain in different figs
            print(f'Plotting {obs_file} vs {file_nwp}')
            for bounds, key in zip((bounds_NOzoom, bounds_zoom), ('', '_zoom')):
                fig = plt.figure(0, figsize = (17.0 / 2.54, 9.0 / 2.54), dpi = 600, clear = True)

                ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
                PlotMapInAxis(ax1, data_obs, lat_obs, lon_obs, extent = bounds, titleLeft = f'{obsDB}\n', titleRight = datetime.strftime(date_simus_ini + timedelta(hours = forecast), '\nValid: %Y%m%d%H UTC'), cbLabel = f'{exp_var_description} ({exp_var_units})', cmap = colormaps[varRaw]['map'], norm = colormaps[varRaw]['norm'])
                PlotBoundsInAxis(ax1, verif_domain, text = 'verif', color = 'black')
                
                ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
                PlotMapInAxis(ax2, data_nwp, lat_nwp, lon_nwp, extent = bounds, titleLeft = f'{model} [{exp}] (regrid)\n', titleRight = f'\nValid: {init_time}+{str(forecast).zfill(2)} UTC', cbLabel = f'{exp_var_description} ({exp_var_units})', yLeftLabel = False, yRightLabel = True, cmap = colormaps[varRaw]['map'], norm = colormaps[varRaw]['norm'])
                PlotBoundsInAxis(ax2, verif_domain, text = 'verif', color = 'black')

                fig.savefig(f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{model}_{exp}_regrid_vs_{obs}_{init_time}+{str(forecast).zfill(2)}_pcolormesh{key}.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
                plt.close(0)
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
