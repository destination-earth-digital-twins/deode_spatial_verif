import os
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import sys

sys.path.append('scripts/libs/')
from LoadWriteData import LoadConfigFileFromYaml
from dicts import get_data_function, colormaps
from times import set_lead_times
from domains import set_domain_verif
from plots import PlotMapInAxis, plot_verif_domain_in_axis
from miscelanea import list_sorted_files


def main(obs, case, exp):
    print("INFO: RUNNING PLOT REGRID")
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
    print(f'INFO: Load config file for {obs_db} database: \n file name: {obs_filename}; file format: {obs_fileformat}; variable to extract: {obs_var_get}')

    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    bounds_NOzoom = config_case['location']['NOzoom']
    verif_domains = config_case['verif_domain']
    print(f'INFO: Load config file for {case} case study: \n init: {config_case["dates"]["ini"]}; end: {config_case["dates"]["end"]}; domain: {bounds_NOzoom}; verification domains: {verif_domains}')

    # exp data
    config_exp = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']
    print(f'INFO: Load config file for {exp} regridded experiment: \n model: {exp_model}; variable to extract: {var_verif} ({var_verif_description}, in {var_verif_units})')

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

        # check if this init_time is completed
        figures_init_time = list_sorted_files(
            f"PLOTS/side_plots/plots_{obs}/{case}/{exp}/" \
                + f"*_{exp}_regrid_vs_{obs}_{init_time}" \
                + f"+*_pcolormesh.png"
        )
        if len(figures_init_time) != len(lead_times):

            # plot OBS vs Regrid exp at each timestep
            for lead_time in lead_times:
                fig_name = f"PLOTS/side_plots/plots_{obs}/{case}/{exp}/" \
                    + f"{exp_model_in_filename}_{exp}_regrid_vs_{obs}_" \
                    + f"{init_time}+{str(lead_time).zfill(2)}_pcolormesh.png"
                if not os.path.isfile(fig_name):
                    obs_file = datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
                    file_nwp = f'SIMULATIONS/{exp}/data_regrid/{init_time}/{exp_model_in_filename}_{exp}_{var_verif}_{obs_db}grid_{init_time}+{str(lead_time).zfill(2)}.nc'
                    if os.path.isfile(obs_file) and os.path.isfile(file_nwp):
                        data_obs, lat_obs, lon_obs = get_data_function[obs_fileformat](obs_file, [obs_var_get, 'lat', 'lon'])
                        data_nwp, lat_nwp, lon_nwp = get_data_function['netCDF'](file_nwp, [var_verif, 'lat', 'lon'])
            
                        # set verif domain
                        verif_domain = set_domain_verif(date_simus_ini + timedelta(hours = lead_time.item()), verif_domains)
                        if verif_domain is None:
                            verif_domain = [lon_nwp[:, 0].max() + 5.5, lon_nwp[:, -1].min() - 5.5, lat_nwp[0, :].max() + 5.5, lat_nwp[-1, :].min() - 5.5]
                            print(f'INFO: verif domain not established for {datetime.strftime(date_simus_ini + timedelta(hours = lead_time.item()), "%Y%m%d%H")} UTC. By default: {verif_domain}')
            
                        # plot large and small domain in different figs
                        print(f'INFO: Plotting {obs_file} vs {file_nwp}')
                        valid_time = date_simus_ini + timedelta(hours = lead_time.item())
                        fig = plt.figure(0, figsize = (20.0 / 2.54, 11.0 / 2.54), dpi = 600, clear = True)
            
                        ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
                        ax1, cbar1 = PlotMapInAxis(
                            ax = ax1, 
                            data = data_obs, 
                            lat = lat_obs, 
                            lon = lon_obs, 
                            extent = bounds_NOzoom, 
                            title = f'{obs_db}\nValid on {valid_time.strftime("%Y-%m-%d at %Hz")}', 
                            cb_label = f'{var_verif_description} ({var_verif_units})', 
                            cmap = colormaps[var_verif]['map'], 
                            norm = colormaps[var_verif]['norm']
                        )
                        ax1 = plot_verif_domain_in_axis(ax1, verif_domain, lat_obs, lon_obs)
            
                        ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
                        ax2, cbar2 = PlotMapInAxis(
                            ax = ax2, 
                            data = data_nwp, 
                            lat = lat_nwp, 
                            lon = lon_nwp, 
                            extent = bounds_NOzoom, 
                            title = f'{exp_model} [exp: {exp}] (regrid)\nRun: {init_time} UTC\nValid on {valid_time.strftime("%Y-%m-%d at %Hz")} (+{str(lead_time).zfill(2)})', 
                            cb_label = f'{var_verif_description} ({var_verif_units})', 
                            left_grid_label = False, 
                            right_grid_label = True, 
                            cmap = colormaps[var_verif]['map'], 
                            norm = colormaps[var_verif]['norm']
                        )
                        ax2 = plot_verif_domain_in_axis(ax2, verif_domain, lat_nwp, lon_nwp)
            
                        fig.savefig(fig_name, dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
                        plt.close(0)
                    else:
                        print(
                            f"INFO: can not plot regrid. File {obs_file} and/or ",
                            f"{file_nwp} not found"
                        )
                else:
                    print(f"INFO: file {fig_name} already exists. Avoiding plot")
        else:
            print(f"INFO: All plots generated for init: {init_time}. Avoiding plot")
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
