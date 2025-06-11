import os
import numpy as np
import pandas as pd
import seaborn as sns
from datetime import datetime, timedelta
from pysteps import verification
from matplotlib import pyplot as plt
from matplotlib.colors import from_levels_and_colors
import sys

sys.path.append('scripts/libs/')
from namingformatter import NamingFormatter
from miscelanea import str2bool
from LoadWriteData import LoadConfigFileFromYaml, LoadPickle, SavePickle
from times import set_lead_times
from domains import set_domain_verif, CropDomainsFromBounds
from customSAL import SAL, _sal_detect_objects
from dicts import get_grid_function, get_data_function, colormaps
from plots import plot_fss_scores, plot_sal, plot_detected_objects

offset = {'bt': 0}
fss = verification.get_method("FSS")

def PixelToDistanceStr(nPixels, resolution):
    valueStr, units = resolution.split(' ')
    value = float(valueStr)
    if value < 1.0:
        return f'{round(nPixels * value, 2)} {units}'
    else:
        return f'{int(round(nPixels * value, 0))} {units}'

def main(obs, case, exp, relative_indexed_path, replace_bool):
    print("INFO: RUNNING SPATIAL VERIFICATION")
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')

    # observation database info
    print(f"INFO: Loading OBS YAML file: config/obs_db/config_{obs_db}.yaml")
    config_obs_db = LoadConfigFileFromYaml(
        f'config/obs_db/config_{obs_db}.yaml'
    )
    obs_filename = config_obs_db['format']['filename'][var_verif]
    obs_fileformat = config_obs_db['format']['fileformat']
    if config_obs_db['vars'][var_verif]['postprocess']:
        obs_var_get = var_verif
    else:
        obs_var_get = config_obs_db['vars'][var_verif]['var']
    obs_res = config_obs_db['vars'][var_verif]['res']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    accum_h = config_obs_db["vars"][var_verif]["verif"]["times"]["accum_hours"]
    freq_verif = config_obs_db["vars"][var_verif]["verif"]["times"]["freq_verif"]
    # update params if accumulated values
    if accum_h > 1:
        obs_filename = f"acc{accum_h}h_{'.'.join(obs_filename.split('.')[:-1])}.nc"
        obs_fileformat = "netCDF"
    print(
        f"INFO: Loaded config file for {obs_db} database:\n "
        f"file name: {obs_filename};\n file format: {obs_fileformat};\n "
        f"var. to get: {obs_var_get} (units: {var_verif_units}, "
        f"spatial res.: {obs_res})"
    )
    
    # Case data: initial date + end date
    print(f"INFO: Loading CASE YAML file: config/Case/{relative_indexed_path}/config_{case}.yaml")
    config_case = LoadConfigFileFromYaml(f'config/Case/{relative_indexed_path}/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    verif_domains = config_case['verif_domain']
    print(
        f"INFO: Loaded config file for {case} case study:\n "
        f'init: {config_case["dates"]["ini"]}; '
        f'end: {config_case["dates"]["end"]};\n '
        f"verification domains: {verif_domains}"
    )

    # exp data
    print(f"INFO: Loading EXP YAML file: config/exp/{relative_indexed_path}/config_{exp}.yaml")
    config_exp = LoadConfigFileFromYaml(f'config/exp/{relative_indexed_path}/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']
    find_min = config_exp['vars'][var_verif]['find_min']
    print(
        f"INFO: Loaded config file for {exp} simulation:\n "
        f"model: {exp_model};\n var. to get: {var_verif}"
    )

    # naming formatter
    formatter = NamingFormatter(obs, case, exp, relative_indexed_path)

    # replace outputs bool
    repl_outputs = str2bool(replace_bool)

    # FSS & SAL params
    thresh = config_obs_db['vars'][var_verif]["verif"]['FSS']['thresholds']
    scales = config_obs_db['vars'][var_verif]["verif"]['FSS']['scales']
    thr_factor = config_obs_db['vars'][var_verif]["verif"]['SAL']['f']
    thr_quantile = config_obs_db['vars'][var_verif]["verif"]['SAL']['q']
    detect_params = config_obs_db['vars'][var_verif]["verif"]['SAL']['tstorm_kwargs']
    if detect_params['max_num_features'] == 'None':
        detect_params.update({'max_num_features': None})
    
    # FSS columns and rows names
    fss_nameCols = [PixelToDistanceStr(nPixel, obs_res) for nPixel in scales]
    fss_nameRows = [f'{thr} {var_verif_units}' for thr in thresh]

    # init times of nwp
    for init_time in config_exp['inits'].keys():

        date_exp_end = config_exp['inits'][init_time]['fcast_horiz']

        # set lead times from experiments
        date_simus_ini = datetime.strptime(init_time, '%Y%m%d%H')
        date_simus_end = datetime.strptime(date_exp_end, '%Y%m%d%H')
        lead_times = set_lead_times(
            date_ini=date_ini,
            date_end=date_end,
            date_sim_init=date_simus_ini,
            date_sim_forecast=date_simus_end,
            freq=freq_verif
        )
        if is_accum:
            lead_times = lead_times[lead_times >= accum_h].copy()
        elif not verif_at_0h:
            lead_times = lead_times[lead_times > 0].copy()
        else:
            pass

        if len(lead_times) > 0:
            print(
                f"INFO: Lead times from {exp}: "
                f"{init_time}+{str(lead_times[0]).zfill(3)} "
                f"({datetime.strftime(date_simus_ini + timedelta(hours=lead_times[0].item()), '%Y%m%d%H')}) "
                f"up to {init_time}+{str(lead_times[-1].item()).zfill(3)} "
                f"({datetime.strftime(date_simus_ini + timedelta(hours=lead_times[-1].item()), '%Y%m%d%H')}) "
                f"with frequency: {freq_verif}h"
            )
    
            file_pickle_fss = formatter.format_string(
                template="pickle_fss", init_time=init_time, acc_h=accum_h
            )
            file_pickle_sal = formatter.format_string(
                template="pickle_sal", init_time=init_time, acc_h=accum_h
            )
            if repl_outputs:
                try:
                    os.remove(file_pickle_fss)
                    os.remove(file_pickle_sal)
                except FileNotFoundError:
                    print(
                        f"INFO: replace_outputs option enabled but verification "
                        f"files not found for init: {init_time}"
                    )
            if os.path.isfile(file_pickle_fss):
                print(f"INFO: Verification scores found for init {init_time}")
                dictFSS = LoadPickle(file_pickle_fss)
                verified_lt = np.array([int(lt_str) for lt_str in dictFSS.keys()])
                pickle_sal = LoadPickle(file_pickle_sal)
                dfSAL = pickle_sal["values"].copy() # Final pandas.dataframe with SAL verification (columns) at each lead time (rows)
                detect_params_old = detect_params.copy()
                for key in detect_params_old.keys():
                    detect_params.update({key: pickle_sal['detect_params'][key]})
            else:
                print(f"INFO: Verification scores NOT found for init {init_time}")
                dictFSS = {} # Final dict with one pandas.dataframe with FSS verification for each lead time
                verified_lt = np.array([])
                pickle_sal = {} # In addition to saving the SAL values, we want to save the object detection parameters.
                pickle_sal['detect_params'] = detect_params.copy()
                pickle_sal['detect_params'].update({
                    'f': thr_factor,
                    'q': thr_quantile,
                })
                dfSAL = pd.DataFrame() # Final pandas.dataframe with SAL verification (columns) at each lead time (rows)
    
            lt_no_verif = lead_times[np.isin(lead_times, verified_lt) == False].copy()
            print(f"INFO: verifying {lt_no_verif} timesteps")
            
            score = {} # this dict will be used to build pandas.dataframe and included them into dictFSS
            listFSS_fcst = []
            for lead_time in lt_no_verif:
                file_obs = datetime.strftime(
                    date_simus_ini + timedelta(hours=lead_time.item()),
                    f'OBSERVATIONS/data_{obs}/{relative_indexed_path}/{case}/{obs_filename}'
                )
                file_nwp = formatter.format_string(
                    template="regrid",
                    init_time=init_time,
                    lead_time=lead_time.item(),
                    acc_h=accum_h
                )
                if os.path.isfile(file_obs) and os.path.isfile(file_nwp):
                    data_obs = get_data_function[obs_fileformat](
                        file_obs, obs_var_get
                    )
                    obs_lat, obs_lon = get_grid_function[obs_fileformat](
                        file_obs
                    )
                    data_nwp = get_data_function['netCDF'](
                        file_nwp, var_verif
                    )
                    lat2D, lon2D = get_grid_function['netCDF'](file_nwp)
        
                    # set verif domain
                    verif_domain = set_domain_verif(
                        date_simus_ini + timedelta(hours=lead_time.item()), 
                        verif_domains
                    )
                    if verif_domain is None:
                        verif_domain = [
                            lon_nwp[:, 0].max() + 0.5,
                            lon_nwp[:, -1].min() - 0.5,
                            lat_nwp[0, :].max() + 0.5,
                            lat_nwp[-1, :].min() - 0.5
                        ]
                        print(
                            "INFO: verif domain not established at "
                            f'{datetime.strftime(date_simus_ini + timedelta(hours=lead_time.item()), "%Y%m%d%H")} '
                            f"UTC. By default: {verif_domain}"
                        )

                    # crop data to common domain
                    data_nwp_common = CropDomainsFromBounds(
                        data_nwp, lat2D, lon2D, verif_domain
                    )
                    data_obs_common = CropDomainsFromBounds(
                        data_obs, obs_lat, obs_lon, verif_domain
                    )

                    # if the minimum values are searched, the array values have to be inverted due to the FSS and SAL methods 
                    # only allow searching for values above the selected thresholds. An offset must be added because 
                    # negative values are filtered out by the object detection algorithm. This offset is hard-coded in this script.
                    if find_min == True:
                        data_nwp_common = -1.0 * data_nwp_common.copy() + offset[var_verif]
                        data_obs_common = -1.0 * data_obs_common.copy() + offset[var_verif]
                        thresh = [-1.0 * thr + offset[var_verif] for thr in thresh]
                        # addapted colorbar only for object detection
                        cmap, norm = from_levels_and_colors(
                            -1.0 * np.flipud(colormaps[var_verif]['norm'].boundaries) + offset[var_verif], 
                            np.flipud(colormaps[var_verif]['map'].colors), 
                            # extend = colormaps[var_verif]['map'].colorbar_extend
                        )
                    else:
                        cmap = colormaps[var_verif]['map']
                        norm = colormaps[var_verif]['norm']

                    # FSS at each lead time
                    score[str(lead_time).zfill(2)] = {}
                    print(
                        'INFO: Compute FSS for timestep '
                        f'{init_time}+{str(lead_time).zfill(3)} '
                        f'({datetime.strftime(date_simus_ini + timedelta(hours=lead_time.item()), "%Y%m%d%H")})\n '
                        f"scales: {fss_nameCols}\n threshold: {fss_nameRows}"
                    )
                    for scale, nameCol in zip(scales, fss_nameCols):
                        score[str(lead_time).zfill(2)][nameCol] = []
                        for thr in thresh:
                            score[str(lead_time).zfill(2)][nameCol].append(
                                fss(
                                    data_nwp_common,
                                    data_obs_common,
                                    thr,
                                    scale
                                )
                            )
                    dictFSS[str(lead_time).zfill(2)] = pd.DataFrame(
                        score[str(lead_time).zfill(2)],
                        index = fss_nameRows
                    )
                    listFSS_fcst.append(
                        dictFSS[str(lead_time).zfill(2)].values.copy()
                    )

                    # plot FSS at each lead time
                    fig, ax = plt.subplots(
                        figsize=(9. / 2.54, 9. / 2.54), clear=True
                    )
                    plot_fss_scores(
                        ax=ax,
                        data=dictFSS[str(lead_time).zfill(2)],
                        title=formatter.format_string(
                            template="title_fss",
                            init_time=init_time,
                            lead_time=lead_time.item()
                        ),
                        x_label = 'Scale',
                        y_label = 'Threshold'
                    )
                    fig.savefig(
                        formatter.format_string(
                            template="plot_fss",
                            init_time=init_time,
                            lead_time=lead_time.item(),
                            acc_h=accum_h
                        ),
                        dpi=600,
                        bbox_inches='tight',
                        pad_inches = 0.05
                    )
                    plt.close()
        
                    # SAL at each lead time
                    print(
                        'INFO: Compute SAL for timestep '
                        f'{init_time}+{str(lead_time).zfill(3)} '
                        f'({datetime.strftime(date_simus_ini + timedelta(hours=lead_time.item()), "%Y%m%d%H")})\n '
                        f"f: {thr_factor};\n q: {thr_quantile};\n "
                        f"detection params: {detect_params}"
                    )
                    objects = {}
                    for k, array in zip(('OBS', 'PRED'), (data_obs_common, data_nwp_common)):
                        objects[k] = _sal_detect_objects(
                            array,
                            thr_factor=thr_factor,
                            thr_quantile=thr_quantile,
                            tstorm_kwargs=detect_params
                        )
                    sValue, aValue, lValue = SAL(
                        data_nwp_common,
                        data_obs_common,
                        thr_factor = thr_factor,
                        thr_quantile = thr_quantile,
                        tstorm_kwargs = detect_params,
                    )

                    dfSALrow = pd.DataFrame(
                        np.array([sValue, aValue, lValue]).reshape(1, 3),
                        columns = ['Structure', 'Amplitude', 'Location'],
                        index = [str(lead_time).zfill(2)]
                    )
                    dfSAL = pd.concat([dfSAL.copy(), dfSALrow.copy()])
        
                    # plot detected objects
                    fig = plot_detected_objects(
                        observation_objects=objects['OBS'],
                        prediction_objects=objects['PRED'],
                        cmap=cmap,
                        norm=norm
                    )
                    fig.savefig(
                        formatter.format_string(
                            template="plot_objects",
                            init_time=init_time,
                            lead_time=lead_time.item(),
                            acc_h=accum_h
                        ),
                        dpi=600, 
                        bbox_inches='tight', 
                        pad_inches=0.05
                    )
        
                    # plot SAL at each lead time
                    figname_sal = formatter.format_string(
                        template="plot_sal",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    if len(dfSALrow.dropna()) > 0:
                        with sns.axes_style('darkgrid'):
                            fig, ax = plt.subplots(
                                figsize=(9. / 2.54, 9. / 2.54), clear=True
                            )
                            _ = plot_sal(
                                ax=ax, 
                                structures=dfSAL.loc[
                                    str(lead_time).zfill(2), 'Structure'
                                ], 
                                amplitudes=dfSAL.loc[
                                    str(lead_time).zfill(2), 'Amplitude'
                                ], 
                                locations=dfSAL.loc[
                                    str(lead_time).zfill(2), 'Location'
                                ], 
                                title=formatter.format_string(
                                    template="title_sal",
                                    init_time=init_time,
                                    lead_time=lead_time.item()
                                ),
                                detect_params={
                                    "f": thr_factor,
                                    "q": thr_quantile,
                                    "minsize": detect_params["minsize"],
                                    "mindis": detect_params["mindis"]
                                }
                            )
                            fig.savefig(
                                figname_sal, 
                                dpi=600, 
                                bbox_inches='tight', 
                                pad_inches = 0.05
                            )
                            plt.close()
                    elif os.path.isfile(figname_sal):
                        print(
                            "INFO: no objects detected for "
                            f"{init_time}+{str(lead_time).zfill(2)}. "
                            "Removing the previous file for clarity"
                        )
                        os.remove(figname_sal)
                    else:
                        print(
                            "INFO: no objects detected for "
                            f"{init_time}+{str(lead_time).zfill(2)}"
                        )
                else:
                    print(
                        f"INFO: Files '{file_obs}' and/or '{file_nwp}' not "
                        "found.\n It is not possible to conduct the spatial "
                        "verification for timestep: "
                        f"{init_time}+{str(lead_time).zfill(2)}"
                    )
    
            verified_lt = np.array([int(lt_str) for lt_str in dictFSS.keys()]) # update lead times verified
            try:
                verif_complete = (verified_lt == lead_times).all()
            except ValueError:
                verif_complete = False
            if verif_complete:
                # plot and save FSS and SAL verifications (mean and all, respectively)
                dfFSS_mean = pd.DataFrame(
                    np.nanmean(listFSS_fcst, axis=0),
                    index = dictFSS[tuple(dictFSS.keys())[0]].index,
                    columns = dictFSS[tuple(dictFSS.keys())[0]].columns
                )
                fig, ax = plt.subplots(
                    figsize=(9. / 2.54, 9. / 2.54), clear=True
                )
                plot_fss_scores(
                    ax=ax,
                    data=dfFSS_mean,
                    title=formatter.format_string(
                        template="title_fss_period",
                        init_time=init_time,
                        lead_time=list(lead_times)
                    ),
                    x_label = 'Scale',
                    y_label = 'Threshold'
                )
                fig.savefig(
                    formatter.format_string(
                        template="plot_fss_init",
                        init_time=init_time,
                        acc_h=accum_h
                    ),
                    dpi=600, 
                    bbox_inches='tight', 
                    pad_inches=0.05
                )
                plt.close()

                with sns.axes_style('darkgrid'):
                    fig, ax = plt.subplots(
                        figsize=(9. / 2.54, 9. / 2.54), clear=True
                    )
                    _ = plot_sal(
                        ax=ax, 
                        structures=dfSAL.dropna()['Structure'].values,
                        amplitudes=dfSAL.dropna()['Amplitude'].values,
                        locations=dfSAL.dropna()['Location'].values,
                        title=formatter.format_string(
                            template="title_sal_period",
                            init_time=init_time,
                            lead_time=list(lead_times)
                        ),
                        detect_params={
                            "f": thr_factor,
                            "q": thr_quantile,
                            "minsize": detect_params["minsize"],
                            "mindis": detect_params["mindis"]
                        }
                    )
                    fig.savefig(
                        formatter.format_string(
                            template="plot_sal_init",
                            init_time=init_time,
                            acc_h=accum_h
                        ),
                        dpi=600, 
                        bbox_inches='tight', 
                        pad_inches=0.05
                    )
                    plt.close()

            # save pickles
            dictFSS_sort = dict(sorted(dictFSS.items()))
            pickle_fss_name = formatter.format_string(
                "pickle_fss", init_time=init_time, acc_h=accum_h
            )
            SavePickle(
                dictFSS,
                pickle_fss_name
            )
            print(f"INFO: file {pickle_fss_name} saved")
            dfSAL.sort_index(inplace=True)
            pickle_sal['values'] = dfSAL.copy()
            pickle_sal_name = formatter.format_string(
                "pickle_sal", init_time=init_time, acc_h=accum_h
            )
            SavePickle(
                pickle_sal,
                pickle_sal_name
            )
            print(f"INFO: file {pickle_sal_name} saved")
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3],  sys.argv[4], sys.argv[5])
