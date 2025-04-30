import os
import sys
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from datetime import datetime, timedelta
from glob import glob

sys.path.append('scripts/libs/')
from namingformatter import NamingFormatter
from LoadWriteData import LoadConfigFileFromYaml, LoadPickle
from dicts import get_data_function, get_grid_function, postprocess_function, colormaps
from times import lead_time_replace, set_lead_times
from domains import set_domain_verif
from miscelanea import list_sorted_files
from plots import PlotMapInAxis, plot_verif_domain_in_axis, plot_domain_in_axis
from colormaps import ecmwf_accum_pcp_cmap_2, ecmwf_accum_pcp_norm_2

def main(obs, case, exps, relative_indexed_path):
    print("INFO: RUNNING COMPARISON: MAPS")
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')
    if ((var_verif == 'pcp') | (var_verif == 'rain')):
        key = 'Total'
    elif var_verif == 'bt':
        key = 'Min'
    else:
        key = 'Max'

    # observation database info
    print(f"INFO: Loading OBS YAML file: config/obs_db/config_{obs_db}.yaml")
    config_obs_db = LoadConfigFileFromYaml(
        f"config/obs_db/config_{obs_db}.yaml"
    )
    obs_filename = config_obs_db['format']['filename'][var_verif]
    obs_fileformat = config_obs_db['format']['fileformat']
    if config_obs_db['vars'][var_verif]['postprocess']:
        obs_var_get = var_verif
    else:
        obs_var_get = config_obs_db['vars'][var_verif]['var']
    var_verif_description = config_obs_db['vars'][var_verif]['description']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    accum_h = config_obs_db["vars"][var_verif]["verif"]["times"]["accum_hours"]
    #freq_verif = config_obs_db["vars"][var_verif]["verif"]["times"]["freq_verif"]
    print(
        f"INFO: Loaded config file for {obs_db} database:\n "
        f"file name: {obs_filename};\n file format: {obs_fileformat};\n "
        f"var. to get: {obs_var_get} ({var_verif_description}, "
        f"in {var_verif_units})"
    )

    # Case data
    print(
        "INFO: Loading CASE YAML file: "
        f"config/Case/{relative_indexed_path}/config_{case}.yaml"
    )
    config_case = LoadConfigFileFromYaml(
        f'config/Case/{relative_indexed_path}/config_{case}.yaml'
    )
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    case_domain = config_case['location']['NOzoom']
    verif_domains = config_case['verif_domain']
    print(
        f"INFO: Loaded config file for {case} case study:\n "
        f'init: {config_case["dates"]["ini"]}; '
        f'end: {config_case["dates"]["end"]}'
        f"domain: {case_domain};\n verification domains: {verif_domains}"
    )

    # naming formatters
    formatter = {}

    # Experiments to compare between. Load fss to set common init times
    configs_exps, lead_times_inits_exps, date_exps_end = {}, {}, {}
    expLowRes, expHighRes = exps.split('-VS-')
    for exp in (expLowRes, expHighRes):
        print(
            "INFO: Loading EXP YAML file: "
            f"config/exp/{relative_indexed_path}/config_{exp}.yaml"
        )
        configs_exps[exp] = LoadConfigFileFromYaml(
            f'config/exp/{relative_indexed_path}/config_{exp}.yaml'
        )
        print(f"INFO: Loaded config file for {exp} simulation")
        lead_times_inits_exps[exp] = {}
        date_exps_end[exp] = {}
        formatter[exp] = NamingFormatter(obs, case, exp, relative_indexed_path)
        for init_time in configs_exps[exp]['inits'].keys():
            date_exps_end[exp][init_time] = configs_exps[exp]['inits'][init_time]['fcast_horiz']
            file_fss = formatter[exp].format_string(
                template="pickle_fss", init_time=init_time, acc_h=accum_h
            )
            try:
                fss_scores = LoadPickle(file_fss)
                print(f"INFO: pickle '{file_fss}' loaded")
                lead_times_inits_exps[exp][init_time] = tuple(fss_scores.keys())
            except FileNotFoundError:
                print(f"INFO: pickle '{file_fss}' not found.")

    # common inits with verifications
    mask_isin = np.isin(
        list(lead_times_inits_exps[expLowRes].keys()),
        list(lead_times_inits_exps[expHighRes].keys())
    )
    common_inits = np.array(
        list(lead_times_inits_exps[expLowRes].keys())
    )[mask_isin].copy()
    print(f"INFO: common inits: {common_inits}")

    # loop for common inits
    for iterator, init_time in enumerate(common_inits):
        # times
        date_exp_ini = datetime.strptime(init_time, '%Y%m%d%H')
        date_simus_end = min(
            datetime.strptime(date_exps_end[expLowRes][init_time], "%Y%m%d%H"),
            datetime.strptime(date_exps_end[expHighRes][init_time], "%Y%m%d%H")
        )
        lead_times = set_lead_times(
            date_ini=date_ini,
            date_end=date_end,
            date_sim_init=date_exp_ini,
            date_sim_forecast=date_simus_end
        )
        if len(lead_times) == 1:
            if accum_h <= 1:
                raise ValueError(
                    f"accum must be higher than 1 or init case != end case"
                )
            lead_times = np.arange(lead_times[0] - accum_h, lead_times[0] + 1)
        lead_time_ini = lead_times[0]
        lead_time_end = lead_times[-1]
        fig_total_name = (
            f"PLOTS/main_plots/{relative_indexed_path}/{case}/"
            f"{key}_{var_verif}_{case}_{exps.replace('-VS-', '_')}_{obs_db}_"
            f"{init_time}+{str(lead_time_ini.item()).zfill(2)}_"
            f"+{str(lead_time_end.item()).zfill(2)}.png"
        )
        # figure of total/max values
        if not os.path.isfile(fig_total_name):
            print(
                f"INFO: file '{fig_total_name}' not found.\n "
                "Collecting files for plotting..."
            )
            # concatenate arrays for obs and exps
            valid_times = []
            values_exp_lowres = []
            values_obs = []
            values_exp_highres = []
            obs_lat = None
            expLowRes_lat = None
            expHighRes_lat = None
            for lead_time in lead_times:
                valid_time = date_exp_ini + timedelta(hours=lead_time.item())
                valid_times.append(valid_time)
                # name of files
                obs_file = datetime.strftime(
                    valid_time,
                    f'OBSERVATIONS/data_{obs}/{relative_indexed_path}/{case}/{obs_filename}'
                )
                exp_lowres_file = date_exp_ini.strftime(
                    os.path.join(
                        f"SIMULATIONS/{relative_indexed_path}/{expLowRes}/data_orig/{init_time}",
                        lead_time_replace(
                            configs_exps[expLowRes]['format']['filename'],
                            lead_time.item()
                        )
                    )
                )
                exp_highres_file = date_exp_ini.strftime(
                    os.path.join(
                        f"SIMULATIONS/{relative_indexed_path}/{expHighRes}/data_orig/{init_time}",
                        lead_time_replace(
                            configs_exps[expHighRes]['format']['filename'],
                            lead_time.item()
                        )
                    )
                )

                # get lat lon coordinates from obs and exps
                if obs_lat is None:
                    obs_lat, obs_lon = get_grid_function[obs_fileformat](obs_file)
                if expLowRes_lat is None and os.path.isfile(exp_lowres_file):
                    expLowRes_lat, expLowRes_lon = get_grid_function[configs_exps[expLowRes]['format']['fileformat']](
                        exp_lowres_file
                    )
                if expHighRes_lat is None and os.path.isfile(exp_highres_file):
                    expHighRes_lat, expHighRes_lon = get_grid_function[configs_exps[expHighRes]['format']['fileformat']](
                        exp_highres_file
                    )

                # append values
                values_obs.append(
                    get_data_function[obs_fileformat](
                        obs_file,
                        obs_var_get
                    )
                )
                combined_lists = zip(
                    (expLowRes, expHighRes),
                    (exp_lowres_file, exp_highres_file),
                    (values_exp_lowres, values_exp_highres)
                )
                for exp, filename, list_values in combined_lists:
                    if (
                            lead_time.item() > 0 or 
                            (
                                lead_time.item() == 0 and 
                                configs_exps[exp]['vars'][var_verif]['verif_0h']
                            )
                    ):
                        try:
                            values = get_data_function[configs_exps[exp]['format']['fileformat']](
                                filename,
                                configs_exps[exp]['vars'][var_verif]['var']
                            )
                            # check if values must be processed
                            if configs_exps[exp]['vars'][var_verif]['postprocess'] != "None":
                                values_pp = postprocess_function[configs_exps[exp]['vars'][var_verif]['postprocess']](
                                    values
                                )
                            else:
                                values_pp = values.copy()
                            list_values.append(values_pp.copy())
                        except OSError:
                            print(f"INFO: file '{filename}' not found.")

            # plotting
            fig = plt.figure(
                iterator, figsize=(36.0 / 2.54, 11.0 / 2.54), clear=True
            )
            combined_lists = zip(
                range(3),
                (expLowRes, obs_db, expHighRes),
                (values_exp_lowres, values_obs, values_exp_highres),
                (expLowRes_lat, obs_lat, expHighRes_lat),
                (expLowRes_lon, obs_lon, expHighRes_lon),
                (True, False, False),
                (False, False, True)
            )
            for itr, db, values, lat, lon, llabel, rlabel in combined_lists:
                ax = fig.add_subplot(
                    1, 3, itr + 1, projection = ccrs.PlateCarree()
                )
                if itr == 1:
                    title = (
                        f"{db}\nValid from "
                        f'{valid_times[0].strftime("%Y-%m %d-%Hz")} to '
                        f'{valid_times[-1].strftime("%d-%Hz")}'
                    )
                else:
                    title = (
                        f"{configs_exps[db]['model']['name']} [exp: {db}]\n"
                        f"Run: {init_time} UTC\nValid from "
                        f"{valid_times[0].strftime('%Y-%m %d-%Hz')} "
                        f"(+{str(lead_time_ini.item()).zfill(2)}) to "
                        f"{valid_times[-1].strftime('%d-%Hz')} "
                        f"(+{str(lead_time_end.item()).zfill(2)})"
                    )
                if ((var_verif == 'pcp') | (var_verif == 'rain')):
                    if db == obs_db:
                        values_to_plot = np.nansum(values[1:], axis = 0)
                    else:
                        if lead_time_ini.item() == 0:
                            values_to_plot = values[-1].copy()
                        else:
                            values_to_plot = values[-1].copy() - values[0].copy()
                            values_to_plot[values_to_plot < 0.] = 0.
                    n_hours = (lead_time_end - lead_time_ini).item()
                    cb_label = (
                        f'{var_verif_description.replace("1", str(n_hours))} '
                        f"({var_verif_units})"
                    )
                    cmap = ecmwf_accum_pcp_cmap_2
                    norm = ecmwf_accum_pcp_norm_2
                elif var_verif == 'bt':
                    values_to_plot = np.min(values, axis = 0)
                    cb_label = (
                        f"{key}. {var_verif_description} "
                        "({var_verif_units})"
                    )
                    cmap = colormaps[var_verif]['map']
                    norm = colormaps[var_verif]['norm']
                else:
                    values_to_plot = np.max(values, axis = 0)
                    cb_label = (
                        f"{key}. {var_verif_description} "
                        f"({var_verif_units})"
                    )
                    cmap = colormaps[var_verif]['map']
                    norm = colormaps[var_verif]['norm']
                ax, _ = PlotMapInAxis(
                    ax=ax, 
                    data=values_to_plot, 
                    lat=lat, 
                    lon=lon, 
                    extent=case_domain, 
                    title=title, 
                    cb_label=cb_label, 
                    left_grid_label=llabel, 
                    right_grid_label=rlabel, 
                    cmap=cmap, 
                    norm=norm
                )
                if len(verif_domains.keys()) == 1:
                    ax = plot_verif_domain_in_axis(
                        ax, tuple(verif_domains.values())[0], obs_lat, obs_lon
                    )
            fig.savefig(
                fig_total_name,
                dpi=600,
                bbox_inches='tight',
                pad_inches=0.05
            )
            plt.close(iterator)
            print(f"INFO: file '{fig_total_name}' saved")
        else:
            print(f"INFO: file '{fig_total_name}' found. Avoiding plot.")
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
