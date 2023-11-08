#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append('scripts/libs/')
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from datetime import datetime, timedelta
from glob import glob
from LoadWriteData import LoadConfigFileFromYaml, LoadPickle
from dicts import get_data_function, get_grid_function, colormaps
from plots import PlotMapInAxis, PlotContourDomainInAxis, PlotBoundsInAxis

freqHours = 1 # ALL CODE IS DEVELOPED FOR DATA WITH 1 HOUR TIME RESOLUTION
colors_name = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan']

def lead_time_replace(text, replace_with = '*'):
    pattern = r'(%LL+)'
    new_text = re.sub(pattern, lambda match: replace_function(match.group(0), replace_with), text)
    return new_text

def replace_function(text, replace_with):
    if isinstance(replace_with, int):
        return str(replace_with).zfill(len(text) - 1)
    else:
        return "*"

def sorted_list_files(string):
    list_files = glob(string)
    list_files.sort()
    return list_files
    
def main(obs, case, exps):
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
    print(f'Load config file for {obs_db} database: \n file name: {obs_filename}; file format: {obs_fileformat}; var. to get: {obs_var_get}')

    # Case bounds
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    case_domain = config_case['location']['NOzoom']
    print(f'Map bounds: {case_domain}')
    
    # Experiments to compare between. Load fss to set common lead times
    configs_exps, lead_times_inits_exps = {}, {}
    expLowRes, expHighRes = exps.split('-VS-')
    for exp in (expLowRes, expHighRes):
        print(f'Load config file: config/exp/config_{exp}.yaml')
        configs_exps[exp] = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
        lead_times_inits_exps[exp] = {}
        files_fss = sorted_list_files(f"pickles/FSS/{obs}/{case}/{exp}/FSS_{configs_exps[exp]['model']['name']}_{exp}_{obs}_*.pkl")
        for file_fss in files_fss:
            init_time = file_fss.split('_')[-1].split('.')[0]
            fss_scores = LoadPickle(file_fss)
            lead_times_inits_exps[exp][init_time] = tuple(fss_scores.keys())

    # common inits & lead_times
    mask_isin = np.isin(list(lead_times_inits_exps[expLowRes].keys()), list(lead_times_inits_exps[expHighRes].keys()))
    common_inits = np.array(list(lead_times_inits_exps[expLowRes].keys()))[mask_isin].copy()
    common_lead_times = {}
    for init_time in common_inits:
        mask_isin = np.isin(lead_times_inits_exps[expLowRes][init_time], lead_times_inits_exps[expHighRes][init_time])
        common_lead_times[init_time] = np.array(lead_times_inits_exps[expLowRes][init_time])[mask_isin]
        print(f'Set common lead times. {init_time}: {common_lead_times[init_time]}')

    values_databases = {}
    for iterator, init_time in enumerate(common_inits):
        verif_domain_ini = None
        date_exp_ini = datetime.strptime(init_time, '%Y%m%d%H')
        for db in (expLowRes, obs_db, expHighRes):
            values_databases[db] = []

        for lead_time in common_lead_times[init_time]:
            obs_file = datetime.strftime(date_exp_ini + timedelta(hours = int(lead_time)), f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
            obs_values = get_data_function[obs_fileformat](obs_file, [obs_var_get,])
            values_databases[obs_db].append(obs_values.copy())
            lat2D, lon2D = get_grid_function[obs_fileformat](obs_file) # it's the same grid for obs, expLowRes and expHighRes

            expLowRes_file = datetime.strftime(date_exp_ini, f"SIMULATIONS/{expLowRes}/data_regrid/{init_time}/{configs_exps[expLowRes]['model']['name']}_{expLowRes}_{var_verif}_{obs_db}grid_{init_time}+{str(lead_time).zfill(2)}.nc")
            expLowRes_values = get_data_function['netCDF'](expLowRes_file, [var_verif,])
            values_databases[expLowRes].append(expLowRes_values.copy())

            expHighRes_file = datetime.strftime(date_exp_ini, f"SIMULATIONS/{expHighRes}/data_regrid/{init_time}/{configs_exps[expHighRes]['model']['name']}_{expHighRes}_{var_verif}_{obs_db}grid_{init_time}+{str(lead_time).zfill(2)}.nc")
            expHighRes_values = get_data_function['netCDF'](expHighRes_file, [var_verif,])
            values_databases[expHighRes].append(expHighRes_values.copy())
            expHighRes_fileformat = lead_time_replace(configs_exps[expHighRes]['format']['filename'], lead_time)
            expHighRes_file_orig = datetime.strftime(date_exp_ini, f"SIMULATIONS/{expHighRes}/data_orig/{init_time}/{expHighRes_fileformat}")
            lat2D_expHighRes, lon2D_expHighRes = get_grid_function[configs_exps[expHighRes]['format']['fileformat']](expHighRes_file_orig)

            try:
                if configs_exps[expLowRes]['vars'][var_verif]['accum'] == True:
                    verif_domain = config_case['verif_domain'][datetime.strftime(date_exp_ini + timedelta(hours = int(lead_time) - 1), '%Y%m%d%H')]
                else:
                    verif_domain = config_case['verif_domain'][datetime.strftime(date_exp_ini + timedelta(hours = int(lead_time)), '%Y%m%d%H')]
                verif_domain_ini = verif_domain
            except KeyError:
                if verif_domain_ini is not None:
                    verif_domain = verif_domain_ini
                else:
                    verif_domain = [lon2D_expHighRes[:, 0].max() + 0.5, lon2D_expHighRes[:, -1].min() - 0.5, lat2D_expHighRes[0, :].max() + 0.5, lat2D_expHighRes[-1, :].min() - 0.5]
                    print(f'verif domain not established for {datetime.strftime(date_exp_ini + timedelta(hours = int(lead_time)), "%Y%m%d%H")} UTC. By default: {verif_domain}')

            # Build the frame
            print(f'plotting {expLowRes_file} vs {obs_file} vs {expHighRes_file}')
            fig_frame = plt.figure(0, figsize = (24.0 / 2.54, 10.0 / 2.54), clear = True)
            for iterator_axis, array2D, title_left, bool_left_label, bool_righ_label in zip(range(3), [expLowRes_values, obs_values, expHighRes_values], [f"{configs_exps[expLowRes]['model']['name']}[{expLowRes}]", obs_db, f"{configs_exps[expHighRes]['model']['name']}[{expHighRes}]"], [True, False, False], [False, False, True]):
                ax = fig_frame.add_subplot(1, 3, iterator_axis + 1, projection = ccrs.PlateCarree())
                if iterator_axis == 1:
                    title_right = datetime.strftime(date_exp_ini + timedelta(hours = int(lead_time)), 'Valid: %Y%m%d%H UTC')
                    title_color = 'black'
                else:
                    title_right = f'Valid: {init_time}+{str(lead_time).zfill(2)} UTC'
                    title_color = colors_name[iterator]
                PlotMapInAxis(ax, array2D, lat2D, lon2D, extent = case_domain, titleLeft = f'{title_left}\n', titleRight = f'\n{title_right}', cbLabel = f'{var_verif_description} ({var_verif_units})', titleColorRight = title_color, yLeftLabel = bool_left_label, yRightLabel = bool_righ_label, cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
                if iterator_axis == 2:
                    PlotContourDomainInAxis(ax, lat2D_expHighRes, lon2D_expHighRes, text = init_time, color = colors_name[iterator])
                PlotBoundsInAxis(ax, verif_domain, text = 'verif', color = 'black')
            fig_frame.savefig(f"PLOTS/side_plots/plots_verif/gif_frames/{obs}/{case}/{exps.replace('-VS-', '_')}_{obs}_{init_time}+{str(lead_time).zfill(2)}.png", dpi = 300, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close(0)
        
        # figure of total/max values
        fig = plt.figure(1, figsize = (24.0 / 2.54, 10.0 / 2.54), clear = True)
        for iterator_axis, db, bool_left_label, bool_right_label in zip(range(3), list(values_databases.keys()), (True, False, False), (False, False, True)):
            ax = fig.add_subplot(1, 3, iterator_axis + 1, projection = ccrs.PlateCarree())
            if iterator_axis == 1:
                title_right = f"Valid: {config_case['dates']['ini']}-{config_case['dates']['end']} UTC"
                title_color = 'black'
            else:
                title_right = f'Valid: {init_time}+{common_lead_times[init_time][0]} up to +{common_lead_times[init_time][-1]} UTC'
                title_color = colors_name[iterator]
            if var_verif == 'pcp':
                key = 'Total'
                PlotMapInAxis(ax, np.sum(values_databases[db], axis = 0), lat2D, lon2D, extent = case_domain, titleLeft = f'{db}\n', titleRight = f'\n{title_right}', cbLabel = f'{var_verif_description.replace("1", str(len(values_databases[db])))} ({var_verif_units})', titleColorRight = title_color, yLeftLabel = bool_left_label, yRightLabel = bool_right_label, cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
            elif var_verif == 'bt':
                key = 'Min'
                PlotMapInAxis(ax, np.min(values_databases[db], axis = 0), lat2D, lon2D, extent = case_domain, titleLeft = f'{db}\n', titleRight = f'\n{title_right}', cbLabel = f'Min. {var_verif_description} ({var_verif_units})', yLeftLabel = bool_left_label, yRightLabel = bool_right_label, cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
            else:
                key = 'Max'
                PlotMapInAxis(ax, np.max(values_databases[db], axis = 0), lat2D, lon2D, extent = case_domain, titleLeft = f'{db}\n', titleRight = f'\n{title_right}', cbLabel = f'Max. {var_verif_description} ({var_verif_units})', yLeftLabel = bool_left_label, yRightLabel = bool_right_label, cmap = colormaps[var_verif]['map'], norm = colormaps[var_verif]['norm'])
            PlotBoundsInAxis(ax, verif_domain, text = 'verif', color = 'black')
            if iterator_axis == 2:
                PlotContourDomainInAxis(ax, lat2D_expHighRes, lon2D_expHighRes, text = init_time, color = colors_name[iterator])
        fig.savefig(f"PLOTS/main_plots/{case}/{key}_{var_verif}_{case}_{exps.replace('-VS-', '_')}_{obs_db}_{init_time}+{str(common_lead_times[init_time][0]).zfill(2)}_+{str(common_lead_times[init_time][-1]).zfill(2)}.png", dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
        plt.close(1)
    
    # Build the GIF
    gif = []
    images_gif = sorted_list_files(f"PLOTS/side_plots/plots_verif/gif_frames/{obs}/{case}/{exps.replace('-VS-', '_')}_{obs}_*.png")
    for filename in images_gif:
        gif.append(imageio.imread(filename))
    imageio.mimsave(f"PLOTS/main_plots/{case}/{case}_{exps.replace('-VS-', '_')}_{obs}.gif", gif, duration = 0.5)
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
