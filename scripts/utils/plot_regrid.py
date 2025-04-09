import os
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys

sys.path.append('scripts/libs/')
from namingformatter import NamingFormatter
from LoadWriteData import LoadConfigFileFromYaml
from dicts import get_data_function, get_grid_function, colormaps
from times import set_lead_times, lead_time_replace
from domains import set_domain_verif
from plots import PlotMapInAxis, plot_verif_domain_in_axis
from miscelanea import list_sorted_files, str2bool


def main(obs, case, exp, relative_indexed_path, replace_bool):
    print("INFO: RUNNING PLOT REGRID")
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')

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
    freq_verif = config_obs_db["vars"][var_verif]["verif"]["times"]["freq_verif"]
    # update params if accumulated values
    if accum_h > 1:
        obs_filename = f"acc{accum_h}h_{'.'.join(obs_filename.split('.')[:-1])}.nc"
        obs_fileformat = "netCDF"
        var_verif_description = var_verif_description.replace(
            "1-hour", f"{accum_h}-hour"
        )
    print(
        f"INFO: Loaded config file for {obs_db} database:\n "
        f"file name: {obs_filename};\n file format: {obs_fileformat};\n "
        f"var. to get: {obs_var_get} ({var_verif_description}, "
        f"in {var_verif_units})"
    )

    # Case data: initial date + end date
    print(f"INFO: Loading CASE YAML file: config/Case/config_{case}.yaml")
    config_case = LoadConfigFileFromYaml(f'config/Case/{relative_indexed_path}/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    bounds_NOzoom = config_case['location']['NOzoom']
    verif_domains = config_case['verif_domain']
    print(
        f"INFO: Loaded config file for {case} case study:\n "
        f'init: {config_case["dates"]["ini"]}; '
        f'end: {config_case["dates"]["end"]};\n '
        f"domain: {bounds_NOzoom};\n verification domains: {verif_domains}"
    )

    # exp data
    print(f"INFO: Loading EXP YAML file: config/exp/config_{exp}.yaml")
    config_exp = LoadConfigFileFromYaml(f'config/exp/{relative_indexed_path}/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']
    print(
        f"INFO: Loaded config file for {exp} simulation:\n "
        f"model: {exp_model};\n var. to get: {var_verif} "
        f"({var_verif_description}, in {var_verif_units})"
    )

    # naming formatter
    formatter = NamingFormatter(obs, case, exp, relative_indexed_path)

    # replace outputs bool
    repl_outputs = str2bool(replace_bool)

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
                f"INFO: Forecast from {exp}:\n "
                f"{init_time}+{str(lead_times[0]).zfill(3)} "
                f'({datetime.strftime(date_simus_ini + timedelta(hours=lead_times[0].item()), "%Y%m%d%H")}) '
                f"up to {init_time}+{str(lead_times[-1]).zfill(3)} "
                f'({datetime.strftime(date_simus_ini + timedelta(hours=lead_times[-1].item()), "%Y%m%d%H")}) '
                f"with frequency: {freq_verif}h"
            )

            # plot OBS vs Regrid exp at each timestep
            for lead_time in lead_times:
                fig_name = formatter.format_string(
                    template="plot_regrid",
                    init_time=init_time,
                    lead_time=lead_time.item(),
                    acc_h=accum_h
                )
                if not os.path.isfile(fig_name) or repl_outputs:
                    obs_file = datetime.strftime(
                        date_simus_ini + timedelta(hours=lead_time.item()),
                        f"OBSERVATIONS/data_{obs}/{relative_indexed_path}/{case}/{obs_filename}"
                    )
                    file_nwp = formatter.format_string(
                        template="regrid",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    if os.path.isfile(obs_file) and os.path.isfile(file_nwp):
                        data_obs = get_data_function[obs_fileformat](
                            obs_file, obs_var_get
                        )
                        lat_obs, lon_obs = get_grid_function[obs_fileformat](
                            obs_file
                        )
                        data_nwp, lat_nwp, lon_nwp = get_data_function['netCDF'](
                            file_nwp, [var_verif, 'lat', 'lon']
                        )
            
                        # set verif domain
                        verif_domain = set_domain_verif(
                            date_simus_ini + timedelta(hours=lead_time.item()),
                            verif_domains
                        )
                        if verif_domain is None:
                            verif_domain = [
                                lon_nwp[:, 0].max() + 5.5,
                                lon_nwp[:, -1].min() - 5.5,
                                lat_nwp[0, :].max() + 5.5,
                                lat_nwp[-1, :].min() - 5.5
                            ]
                            print(
                                "INFO: verif domain not established at "
                                f'{datetime.strftime(date_simus_ini + timedelta(hours=lead_time.item()), "%Y%m%d%H")} '
                                f"UTC. By default: {verif_domain}"
                            )

                        # plot large and small domain in different figs
                        print(f"INFO: Plotting '{obs_file}' vs '{file_nwp}'")
                        valid_time = date_simus_ini + timedelta(hours=lead_time.item())
                        fig = plt.figure(
                            0,
                            figsize=(20.0 / 2.54, 11.0 / 2.54),
                            dpi=600,
                            clear = True
                        )
                        ax1 = fig.add_subplot(
                            1, 2, 1, projection=ccrs.PlateCarree()
                        )
                        ax1, _ = PlotMapInAxis(
                            ax=ax1,
                            data=data_obs,
                            lat=lat_obs,
                            lon=lon_obs,
                            extent=bounds_NOzoom,
                            title=formatter.format_string(
                                template="title_obs",
                                valid_time=valid_time
                            ),
                            cb_label=(
                                f'{var_verif_description} ({var_verif_units})'
                            ),
                            cmap = colormaps[var_verif]['map'],
                            norm = colormaps[var_verif]['norm']
                        )
                        ax1 = plot_verif_domain_in_axis(
                            ax1, verif_domain, lat_obs, lon_obs
                        )
            
                        ax2 = fig.add_subplot(
                            1, 2, 2, projection=ccrs.PlateCarree()
                        )
                        ax2, _ = PlotMapInAxis(
                            ax=ax2, 
                            data=data_nwp, 
                            lat=lat_nwp, 
                            lon=lon_nwp, 
                            extent=bounds_NOzoom, 
                            title=formatter.format_string(
                                template="title_regrid",
                                valid_time=valid_time,
                                init_time=init_time,
                                lead_time=lead_time.item()
                            ),
                            cb_label = (
                                f'{var_verif_description} ({var_verif_units})'
                            ),
                            left_grid_label=False,
                            right_grid_label=True,
                            cmap = colormaps[var_verif]['map'],
                            norm = colormaps[var_verif]['norm']
                        )
                        ax2 = plot_verif_domain_in_axis(
                            ax2, verif_domain, lat_nwp, lon_nwp
                        )
            
                        fig.savefig(
                            fig_name,
                            dpi=600,
                            bbox_inches='tight',
                            pad_inches=0.05
                        )
                        plt.close(0)
                    else:
                        print(
                            f"INFO: can not plot regrid. File '{obs_file}' "
                            f"and/or '{file_nwp}' not found"
                        )
                else:
                    print(
                        f"INFO: file '{fig_name}' already exists. "
                        "Avoiding plot"
                    )
        else:
            print(
                "INFO: Valid times outside the lead times availables for "
                f"init: {init_time}. Avoiding plot"
            )
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
