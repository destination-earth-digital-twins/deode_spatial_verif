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
from customSAL import SAL
from dicts import get_grid_function, get_data_function, colormaps
from plots import PlotMapInAxis, PlotFSSInAxis, PlotSALinAxis, PlotViolinInAxis

freqHours = 1 # ALL CODE IS DEVELOPED FOR DATA WITH 1 HOUR TIME RESOLUTION

# FSS
fss = verification.get_method("FSS") # NaN == (values >= thr) = [] --> Obs: float; Pred: float; FSS = float | Obs: NaN; Pred: float; FSS = 0.0 | Obs: float; Pred: NaN; FSS = 0.0 | Obs: NaN; Pred: NaN; FSS = NaN

# SAL
#original from pỳsteps: sal = verification.get_method("SAL") # NaN == (values >= thr) = [] --> Obs: float; Pred: float; S, L = float, float | Obs: NaN; Pred: float; S, L = +/-2, NaN | Obs: float; Pred: NaN; S, L = +/-2, NaN | Obs: NaN; Pred: NaN; S, L = NaN, NaN
#rangesSAL = [(0, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 9999.999)]
#colorsSAL = ['tab:green', 'tab:olive', 'gold', 'tab:orange', 'tab:red', 'black']

def CropDomainsFromBounds(data, lat2D, lon2D, bounds):
    lonMin, lonMax, latMin, latMax = bounds
    ids = np.argwhere((lat2D >= latMin) & (lat2D <= latMax) & (lon2D >= lonMin) & (lon2D <= lonMax))
    idLatIni, idLatEnd, idLonIni, idLonEnd = ids[:,0].min(), ids[:,0].max() + 1, ids[:,1].min(), ids[:,1].max() + 1
    return data[idLatIni:idLatEnd, idLonIni:idLonEnd].copy()

def PixelToDistanceStr(nPixels, resolution):
    valueStr, units = resolution.split(' ')
    value = float(valueStr)
    if value < 1.0:
        return f'{round(nPixels * value, 1)} {units}'
    else:
        return f'{int(round(nPixels * value, 0))} {units}'

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
    obsRes = dataObs['vars'][varRaw]['res']
    print(f'Load config file for {obsDB} database: \n file name: {obsFileName}; file format: {obsFileFormat}; variable to extract: {obsVar}')
    
    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H')
    print(f'Load config file for {case} case study: \n init: {dataCase["dates"]["ini"]}; end: {dataCase["dates"]["end"]}; verification domains: {dataCase["verif_domain"]}')

    # exp data
    dataExp = LoadConfigFileFromYaml(f'config/config_{exp}.yaml')
    model = dataExp['model']['name']
    is_negative = dataExp['vars'][varRaw]['negative_values']
    exp_var_units = dataExp['vars'][varRaw]['units']
    print(f'Load config file for {exp} simulation: \n model: {model}; variable to extract: {varRaw} ({dataExp["vars"][varRaw]["description"]}); units: {exp_var_units}')

    # FSS & SAL params
    thresh = dataObs['vars'][varRaw]['FSS']['thresholds']
    scales = dataObs['vars'][varRaw]['FSS']['scales']
    thr_factor = dataObs['vars'][varRaw]['SAL']['f']
    thr_quantile = dataObs['vars'][varRaw]['SAL']['q']
    detect_params = dataObs['vars'][varRaw]['SAL']['tstorm_kwargs']
    if detect_params['max_num_features'] == 'None':
        detect_params.update({'max_num_features': None})
    
    # FSS columns and rows names
    fss_nameCols = [PixelToDistanceStr(nPixel, obsRes) for nPixel in scales]
    if is_negative == True:
        fss_nameRows = [f'-{thr} {exp_var_units}' for thr in thresh]
    else:
        fss_nameRows = [f'{thr} {exp_var_units}' for thr in thresh]

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

        dictFSS = {} # Final dict with one pandas.dataframe with FSS verification for each lead time
        score = {} # this dict will be used to build pandas.dataframe and included them into dictFSS
        dfSAL = pd.DataFrame() # Final pandas.dataframe with SAL verification (columns) at each lead time (rows)

        listFSS_fcst = []
        for forecast in range(forecast_ini, forecast_horiz + 1, freqHours):
            file_obs = datetime.strftime(date_simus_ini + timedelta(hours = forecast), f'OBSERVATIONS/data_{obs}/{case}/{obsFileName}')
            data_obs = get_data_function[obsFileFormat](file_obs, [obsVar])
            file_nwp = f'SIMULATIONS/{exp}/data_regrid/{init_time}/{model}_{exp}_{varRaw}_{obsDB}grid_{init_time}+{str(forecast).zfill(2)}.nc'
            data_nwp = get_data_function['netCDF'](file_nwp, [varRaw])
            lat2D, lon2D = get_grid_function['netCDF'](file_nwp) # it's the same grid for both OBS and exp

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

            # crop data to common domain
            data_nwp_common = CropDomainsFromBounds(data_nwp, lat2D, lon2D, verif_domain)
            data_obs_common = CropDomainsFromBounds(data_obs, lat2D, lon2D, verif_domain)

            # negative vars must be flipped to use FSS and SAL methods
            if is_negative == True:
                data_nwp_common = -1.0 * data_nwp_common.copy()
                data_obs_common = -1.0 * data_obs_common.copy()
                cmap = colormaps[f'inverse_{varRaw}']['map']
                norm = colormaps[f'inverse_{varRaw}']['norm']
            else:
                cmap = colormaps[varRaw]['map']
                norm = colormaps[varRaw]['norm']
            
            # FSS at each lead time
            score[str(forecast).zfill(2)] = {}
            print(f'Compute FSS for timestep {init_time}+{str(forecast).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast), "%Y%m%d%H")}) scales: {fss_nameCols} threshold: {fss_nameRows}')
            for scale, nameCol in zip(scales, fss_nameCols):
                score[str(forecast).zfill(2)][nameCol] = []
                for thr in thresh:
                    score[str(forecast).zfill(2)][nameCol].append(fss(data_nwp_common, data_obs_common, thr, scale))
            dictFSS[str(forecast).zfill(2)] = pd.DataFrame(score[str(forecast).zfill(2)], index = fss_nameRows)
            listFSS_fcst.append(dictFSS[str(forecast).zfill(2)].values.copy())

            # plot FSS at each lead time
            fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
            PlotFSSInAxis(ax, dictFSS[str(forecast).zfill(2)].round(2), title = f'FSS plot \n{model} [{exp}] | {obs} \nValid: {init_time}+{str(forecast).zfill(2)}', xLabel = 'Scale', yLabel = 'Threshold')
            fig.savefig(f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSS_{model}_{exp}_{obs}_{init_time}+{str(forecast).zfill(2)}.png', dpi=600, bbox_inches='tight', pad_inches = 0.05)
            plt.close()

            # SAL at each lead time
            print(f'Compute SAL for timestep {init_time}+{str(forecast).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast), "%Y%m%d%H")}) f: {thr_factor}; q: {thr_quantile}; detection params: {detect_params}')
            sValue, aValue, lValue = SAL(
                data_nwp_common, 
                data_obs_common, 
                thr_factor = thr_factor, 
                thr_quantile = thr_quantile, 
                tstorm_kwargs = detect_params,
                verbose = True, 
                cmap = cmap, 
                norm = norm, 
                figname = f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/DetectedObjects_{obs}_{exp}_{init_time}+{str(forecast).zfill(2)}.png'
            )

            dfSALrow = pd.DataFrame(np.array([sValue, aValue, lValue]).reshape(1, 3), columns = ['Structure', 'Amplitude', 'Location'], index = [str(forecast).zfill(2)])
            dfSAL = pd.concat([dfSAL.copy(), dfSALrow.copy()])

            # plot SAL at each lead time
            if len(dfSALrow.dropna()) > 0:
                with sns.axes_style('darkgrid'):
                    fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
                    PlotSALinAxis(ax, dfSAL.loc[str(forecast).zfill(2), 'Structure'], dfSAL.loc[str(forecast).zfill(2), 'Amplitude'], dfSAL.loc[str(forecast).zfill(2), 'Location'], title = f'SAL plot \n{model} [{exp}] | {obs} \nValid: {init_time}+{forecast}')
                    fig.savefig(f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SAL_{model}_{exp}_{obs}_{init_time}+{str(forecast).zfill(2)}.png', dpi=600, bbox_inches='tight', pad_inches = 0.05)   
                    plt.close()
        
        # plot and save FSS and SAL verifications (mean and all, respectively)
        dfFSS_mean = pd.DataFrame(np.nanmean(listFSS_fcst, axis = 0), index = dictFSS[tuple(dictFSS.keys())[0]].index, columns = dictFSS[tuple(dictFSS.keys())[0]].columns)
        fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
        PlotFSSInAxis(ax, dfFSS_mean.round(2), title = f'FSS plot \n{model} [{exp}] | {obs} \nValid: {init_time}+{str(forecast_ini).zfill(2)}-{init_time}+{str(forecast_horiz).zfill(2)}', xLabel = 'Scale', yLabel = 'Threshold')
        fig.savefig(f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSS_{model}_{exp}_{obs}_{init_time}_mean.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
        plt.close()
        SavePickle(dictFSS, f'pickles/FSS/{obs}/{case}/{exp}/FSS_{model}_{exp}_{obs}_{init_time}')
        
        with sns.axes_style('darkgrid'):
            fig, ax = plt.subplots(figsize = (9. / 2.54, 9. / 2.54), clear = True)
            PlotSALinAxis(ax, dfSAL.dropna()['Structure'].values, dfSAL.dropna()['Amplitude'].values, dfSAL.dropna()['Location'].values, title = f'SAL plot \n{model} [{exp}] | {obs} \nValid: {init_time}+{str(forecast_ini).zfill(2)}-{init_time}+{str(forecast_horiz).zfill(2)}')
            fig.savefig(f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SAL_{model}_{exp}_{obs}_{init_time}_all.png', dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)   
            plt.close()
            SavePickle(dfSAL, f'pickles/SAL/{obs}/{case}/{exp}/SAL_{model}_{exp}_{obs}_{init_time}')

        # violin plot FSS
        with sns.axes_style('whitegrid'):
            fig = plt.figure(figsize=(14 / 2.54, 6.0 * len(thresh) / 2.54), clear = True)
            for iterator, row in enumerate(fss_nameRows):
                fssValuesFixedThres = {}
                for column in fss_nameCols:
                    fssValuesFixedThres[column] = []
                    for forecast in dictFSS.keys():
                        fssValuesFixedThres[column].append(dictFSS[forecast].loc[row, column])
                df = pd.DataFrame(fssValuesFixedThres)
                ax = fig.add_subplot(len(thresh), 1, iterator + 1)
                if iterator == 0:
                    PlotViolinInAxis(ax, df, title = f'FSS distribution - {model} | {exp} | {obs} | {init_time}', yLabel = f'FSS {row}')
                elif iterator == (len(thresh) - 1):
                    PlotViolinInAxis(ax, df, xLabel = f'Scale', yLabel = f'FSS {row}')
                else:
                    PlotViolinInAxis(ax, df, yLabel = f'FSS {row}')
            fig.savefig(f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSSdist_{model}_{exp}_{obs}_{init_time}.png', dpi = 300, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close()
        
        # violin plot SAL
        with sns.axes_style('whitegrid'):
            fig, ax = plt.subplots(figsize=(14. / 2.54, 6.0 / 2.54), clear = True)
            PlotViolinInAxis(ax, dfSAL, title = f'SAL distribution - {model} | {exp} | {obs} | {init_time}', yLabel = 'SAL', yLim = [-2.1, 2.1])
            fig.savefig(f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SALdist_{model}_{exp}_{obs}_{init_time}.png', dpi = 300, bbox_inches = 'tight', pad_inches = 0.05)
            plt.close()
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
