#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('scripts/libs/')
import numpy as np
import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta
from pysteps import verification
from matplotlib import pyplot as plt

from LoadWriteData import LoadConfigFileFromYaml, SavePickle
from times import set_lead_times
from domains import set_domain_verif, CropDomainsFromBounds
from customSAL import SAL
from dicts import get_grid_function, get_data_function, colormaps
from plots import PlotMapInAxis, PlotFSSInAxis, PlotSALinAxis, PlotViolinInAxis

fss = verification.get_method("FSS")

def PixelToDistanceStr(nPixels, resolution):
    valueStr, units = resolution.split(' ')
    value = float(valueStr)
    if value < 1.0:
        return f'{round(nPixels * value, 1)} {units}'
    else:
        return f'{int(round(nPixels * value, 0))} {units}'

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
    obs_res = config_obs_db['vars'][var_verif]['res']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    print(f'Load config file for {obs_db} database: \n file name: {obs_filename}; file format: {obs_fileformat}; variable to extract: {obs_var_get}')
    
    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    verif_domains = config_case['verif_domain']
    print(f'Load config file for {case} case study: \n init: {config_case["dates"]["ini"]}; end: {config_case["dates"]["end"]}; verification domains: {verif_domains}')

    # exp data
    config_exp = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']
    is_negative = config_exp['vars'][var_verif]['negative_values']
    print(f'Load config file for {exp} simulation: \n model: {exp_model}; variable to extract: {var_verif} ({config_obs_db["vars"][var_verif]["description"]}); units: {var_verif_units}')

    # FSS & SAL params
    thresh = config_obs_db['vars'][var_verif]['FSS']['thresholds']
    scales = config_obs_db['vars'][var_verif]['FSS']['scales']
    thr_factor = config_obs_db['vars'][var_verif]['SAL']['f']
    thr_quantile = config_obs_db['vars'][var_verif]['SAL']['q']
    detect_params = config_obs_db['vars'][var_verif]['SAL']['tstorm_kwargs']
    if detect_params['max_num_features'] == 'None':
        detect_params.update({'max_num_features': None})
    
    # FSS columns and rows names
    fss_nameCols = [PixelToDistanceStr(nPixel, obs_res) for nPixel in scales]
    if is_negative == True:
        fss_nameRows = [f'-{thr} {var_verif_units}' for thr in thresh]
    else:
        fss_nameRows = [f'{thr} {var_verif_units}' for thr in thresh]

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

        dictFSS = {} # Final dict with one pandas.dataframe with FSS verification for each lead time
        score = {} # this dict will be used to build pandas.dataframe and included them into dictFSS
        dfSAL = pd.DataFrame() # Final pandas.dataframe with SAL verification (columns) at each lead time (rows)

        listFSS_fcst = []
        for lead_time in lead_times:
            file_obs = datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
            data_obs = get_data_function[obs_fileformat](file_obs, [obs_var_get])
            obs_lat, obs_lon = get_grid_function[obs_fileformat](file_obs)
            file_nwp = f'SIMULATIONS/{exp}/data_regrid/{init_time}/{exp_model_in_filename}_{exp}_{var_verif}_{obs_db}grid_{init_time}+{str(lead_time).zfill(2)}.nc'
            data_nwp = get_data_function['netCDF'](file_nwp, [var_verif])
            lat2D, lon2D = get_grid_function['netCDF'](file_nwp)

            # set verif domain
            verif_domain = set_domain_verif(date_simus_ini + timedelta(hours = lead_time.item()), verif_domains)
            if verif_domain is None:
                verif_domain = [lon_nwp[:, 0].max() + 0.5, lon_nwp[:, -1].min() - 0.5, lat_nwp[0, :].max() + 0.5, lat_nwp[-1, :].min() - 0.5]
                print(f'verif domain not established for {datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), "%Y%m%d%H")} UTC. By default: {verif_domain}')

            # crop data to common domain
            data_nwp_common = CropDomainsFromBounds(data_nwp, lat2D, lon2D, verif_domain)
            data_obs_common = CropDomainsFromBounds(data_obs, obs_lat, obs_lon, verif_domain)

            # negative vars must be flipped to use FSS and SAL methods
            if is_negative == True:
                data_nwp_common = -1.0 * data_nwp_common.copy()
                data_obs_common = -1.0 * data_obs_common.copy()
                cmap = colormaps[f'inverse_{var_verif}']['map']
                norm = colormaps[f'inverse_{var_verif}']['norm']
            else:
                cmap = colormaps[var_verif]['map']
                norm = colormaps[var_verif]['norm']
            
            # FSS at each lead time
            score[str(lead_time).zfill(2)] = {}
            print(f'Compute FSS for timestep {init_time}+{str(lead_time).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), "%Y%m%d%H")}) scales: {fss_nameCols} threshold: {fss_nameRows}')
            for scale, nameCol in zip(scales, fss_nameCols):
                score[str(lead_time).zfill(2)][nameCol] = []
                for thr in thresh:
                    score[str(lead_time).zfill(2)][nameCol].append(fss(data_nwp_common, data_obs_common, thr, scale))
            dictFSS[str(lead_time).zfill(2)] = pd.DataFrame(score[str(lead_time).zfill(2)], index = fss_nameRows)
            listFSS_fcst.append(dictFSS[str(lead_time).zfill(2)].values.copy())

            # plot FSS at each lead time
            fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
            PlotFSSInAxis(ax, dictFSS[str(lead_time).zfill(2)].round(2), title = f'FSS plot \n{exp_model} [{exp}] | {obs} \nValid: {init_time}+{str(lead_time).zfill(2)}', xLabel = 'Scale', yLabel = 'Threshold')
            fig.savefig(f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSS_{exp_model_in_filename}_{exp}_{obs}_{init_time}+{str(lead_time).zfill(2)}.png', dpi=600, bbox_inches='tight', pad_inches = 0.05)
            plt.close()

            # SAL at each lead time
            print(f'Compute SAL for timestep {init_time}+{str(lead_time).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), "%Y%m%d%H")}) f: {thr_factor}; q: {thr_quantile}; detection params: {detect_params}')
            sValue, aValue, lValue = SAL(
                data_nwp_common, 
                data_obs_common, 
                thr_factor = thr_factor, 
                thr_quantile = thr_quantile, 
                tstorm_kwargs = detect_params,
                verbose = True, 
                cmap = cmap, 
                norm = norm, 
                figname = f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/DetectedObjects_{obs}_{exp}_{init_time}+{str(lead_time).zfill(2)}.png'
            )

            dfSALrow = pd.DataFrame(np.array([sValue, aValue, lValue]).reshape(1, 3), columns = ['Structure', 'Amplitude', 'Location'], index = [str(lead_time).zfill(2)])
            dfSAL = pd.concat([dfSAL.copy(), dfSALrow.copy()])

            # plot SAL at each lead time
            if len(dfSALrow.dropna()) > 0:
                with sns.axes_style('darkgrid'):
                    fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
                    PlotSALinAxis(ax, dfSAL.loc[str(lead_time).zfill(2), 'Structure'], dfSAL.loc[str(lead_time).zfill(2), 'Amplitude'], dfSAL.loc[str(lead_time).zfill(2), 'Location'], title = f'SAL plot \n{exp_model} [{exp}] | {obs} \nValid: {init_time}+{lead_time}')
                    fig.savefig(f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SAL_{exp_model_in_filename}_{exp}_{obs}_{init_time}+{str(lead_time).zfill(2)}.png', dpi=600, bbox_inches='tight', pad_inches = 0.05)   
                    plt.close()
        
        # plot and save FSS and SAL verifications (mean and all, respectively)
        dfFSS_mean = pd.DataFrame(np.nanmean(listFSS_fcst, axis = 0), index = dictFSS[tuple(dictFSS.keys())[0]].index, columns = dictFSS[tuple(dictFSS.keys())[0]].columns)
        fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
        PlotFSSInAxis(ax, dfFSS_mean.round(2), title = f'FSS plot \n{exp_model} [{exp}] | {obs} \nValid: {init_time}+{str(lead_times[0]).zfill(2)}-{init_time}+{str(lead_times[-1]).zfill(2)}', xLabel = 'Scale', yLabel = 'Threshold')
        fig.savefig(f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSS_{exp_model_in_filename}_{exp}_{obs}_{init_time}_mean.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
        plt.close()
        SavePickle(dictFSS, f'pickles/FSS/{obs}/{case}/{exp}/FSS_{exp_model_in_filename}_{exp}_{obs}_{init_time}')
        
        with sns.axes_style('darkgrid'):
            fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
            PlotSALinAxis(ax, dfSAL.dropna()['Structure'].values, dfSAL.dropna()['Amplitude'].values, dfSAL.dropna()['Location'].values, title = f'SAL plot \n{exp_model} [{exp}] | {obs} \nValid: {init_time}+{str(lead_times[0]).zfill(2)}-{init_time}+{str(lead_times[-1]).zfill(2)}')
            fig.savefig(f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SAL_{exp_model_in_filename}_{exp}_{obs}_{init_time}_all.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)   
            plt.close()
            SavePickle(dfSAL, f'pickles/SAL/{obs}/{case}/{exp}/SAL_{exp_model_in_filename}_{exp}_{obs}_{init_time}')

        # violin plot FSS
        with sns.axes_style('whitegrid'):
            fig = plt.figure(figsize=(14 / 2.54, 6.0 * len(thresh) / 2.54), clear = True)
            for iterator, row in enumerate(fss_nameRows):
                fssValuesFixedThres = {}
                for column in fss_nameCols:
                    fssValuesFixedThres[column] = []
                    for lead_time in dictFSS.keys():
                        fssValuesFixedThres[column].append(dictFSS[lead_time].loc[row, column])
                df = pd.DataFrame(fssValuesFixedThres)
                ax = fig.add_subplot(len(thresh), 1, iterator + 1)
                if iterator == 0:
                    PlotViolinInAxis(ax, df, title = f'FSS distribution - {exp_model} | {exp} | {obs} | {init_time}', yLabel = f'FSS {row}')
                elif iterator == (len(thresh) - 1):
                    PlotViolinInAxis(ax, df, xLabel = f'Scale', yLabel = f'FSS {row}')
                else:
                    PlotViolinInAxis(ax, df, yLabel = f'FSS {row}')
            fig.savefig(f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSSdist_{exp_model_in_filename}_{exp}_{obs}_{init_time}.png', dpi = 300, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close()
        
        # violin plot SAL
        with sns.axes_style('whitegrid'):
            fig, ax = plt.subplots(figsize=(14. / 2.54, 6.0 / 2.54), clear = True)
            PlotViolinInAxis(ax, dfSAL, title = f'SAL distribution - {exp_model} | {exp} | {obs} | {init_time}', yLabel = 'SAL', yLim = [-2.1, 2.1])
            fig.savefig(f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SALdist_{exp_model_in_filename}_{exp}_{obs}_{init_time}.png', dpi = 300, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close()
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
