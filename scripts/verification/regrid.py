import os
import numpy as np
import cartopy.crs as ccrs
from datetime import datetime, timedelta
from scipy.interpolate import griddata
from matplotlib import pyplot as plt
import sys

sys.path.append('scripts/libs/')
from namingformatter import NamingFormatter
from miscelanea import check_is_empty_dir
from LoadWriteData import LoadConfigFileFromYaml, build_dataset
from times import set_lead_times, lead_time_replace
from domains import CropDomainsFromBounds
from dicts import get_grid_function, get_data_function, colormaps, postprocess_function
from plots import PlotMapInAxis


def main(obs, case, exp):
    print("INFO: RUNNING REGRID EXPERIMENT")
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')
    pattern_to_find = f"*{var_verif}_{obs_db}grid_{case}*.nc"  

    # observation database info
    print("INFO: Loading OBS YAML file: config/obs_db/config_{obs_db}.yaml")
    config_obs_db = LoadConfigFileFromYaml(f'config/obs_db/config_{obs_db}.yaml')
    obs_filename = config_obs_db['format']['filename'][var_verif]
    obs_fileformat = config_obs_db['format']['fileformat']
    if config_obs_db['vars'][var_verif]['postprocess'] == True:
        obs_var_get = var_verif
    else:
        obs_var_get = config_obs_db['vars'][var_verif]['var']
    var_verif_description = config_obs_db['vars'][var_verif]['description']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    print(f'INFO: Loaded config file for {obs_db} database: \n file name: {obs_filename}; file format: {obs_fileformat}; var. to get: {obs_var_get} ({var_verif_description}, in {var_verif_units})')

    # Case data: initial date + end date
    print("INFO: Loading CASE YAML file: config/Case/config_{case}.yaml")
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    case_domain = config_case['location']['NOzoom']
    bounds_W, bounds_E, bounds_S, bounds_N = case_domain
    print(f'INFO: Loaded config file for {case} case study: \n init: {config_case["dates"]["ini"]}; end: {config_case["dates"]["end"]}')

    # exp data
    print("INFO: Loading EXP YAML file: config/exp/config_{exp}.yaml")
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
    print(f'INFO: Load config file for {exp} simulation: \n model: {exp_model}; file paths: {exp_filepaths}; file name: {exp_filename}; file format: {exp_fileformat}; var. to get: {exp_var_get} ({var_verif})')

    # naming formatter
    formatter = NamingFormatter(obs, case, exp)
    
    # init times of nwp
    for init_time in config_exp['inits'].keys():

        date_exp_end = config_exp['inits'][init_time]['fcast_horiz']
        simus_lat = None
        simus_lon = None

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

        if len(lead_times) > 0:
            print(f'INFO: Lead times from {exp}: {init_time}+{str(lead_times[0]).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_times[0].item()), "%Y%m%d%H")}) up to {init_time}+{str(lead_times[-1].item()).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = lead_times[-1].item()), "%Y%m%d%H")})')

            for lead_time in lead_times:
                file_regrid = formatter.format_string(
                    "regrid", init_time=init_time, lead_time=lead_time.item()
                )
                if not os.path.isfile(file_regrid):
                    # link original simus to SIMULATIONS/
                    files_orig_path = exp_filepaths[config_exp['inits'][init_time]['path']].replace('%exp', exp)
                    exp_filename_t = lead_time_replace(exp_filename, lead_time.item())
                    exp_origin = os.path.join(
                        datetime.strftime(date_simus_ini, files_orig_path), 
                        exp_filename_t
                    )
                    os.system(f'ln -s {exp_origin} SIMULATIONS/{exp}/data_orig/{init_time}/')

                    # check lat-lon coordinates from original exps are already retrieved
                    if simus_lat is None and simus_lon is None:
                        obs_file = datetime.strftime(date_ini, f'OBSERVATIONS/data_{obs}/{case}/{obs_filename}')
                        simus_file = datetime.strftime(date_simus_ini, f'SIMULATIONS/{exp}/data_orig/{init_time}/{exp_filename_t}')
                        obs_lat_orig, obs_lon_orig = get_grid_function[obs_fileformat](obs_file)
                        simus_lat_orig, simus_lon_orig = get_grid_function[exp_fileformat](simus_file)

                        # crop data to avoid ram issues
                        obs_lat = CropDomainsFromBounds(obs_lat_orig, obs_lat_orig, obs_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
                        obs_lon = CropDomainsFromBounds(obs_lon_orig, obs_lat_orig, obs_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
                        simus_lat = CropDomainsFromBounds(simus_lat_orig, simus_lat_orig, simus_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
                        simus_lon = CropDomainsFromBounds(simus_lon_orig, simus_lat_orig, simus_lon_orig, [bounds_W - 5., bounds_E + 5., bounds_S - 5., bounds_N + 5.])
                        print(f'INFO: Lat lon coordinates from {obs_db}: \n --- lat --- \n{obs_lat} \n --- lon --- \n{obs_lon}')
                        print(f'INFO: Lat lon coordinates from {exp}: \n --- lat --- \n{simus_lat} \n --- lon --- \n{simus_lon}')

                    if ((is_accum == True) & (lead_time > 1)): # TODO: accum_hours instead 1h
                        # link original simus to SIMULATIONS/
                        exp_filename_dt = lead_time_replace(exp_filename, lead_time.item() - 1) # TODO: accum_hours instead 1h
                        exp_origin_dt = os.path.join(
                            datetime.strftime(date_simus_ini, files_orig_path), 
                            exp_filename_dt
                        )
                        os.system(f'ln -s {exp_origin_dt} SIMULATIONS/{exp}/data_orig/{init_time}/')

                        # example: pcp(t) = tp(t) - tp(t-1); where pcp is 1-hour accumulated precipitation and tp the total precipitation
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
                    if postprocess != "None":
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
                        title = formatter.format_string(
                            template="title_orig",
                            valid_time=valid_time,
                            init_time=init_time,
                            lead_time=lead_time.item()
                        ),
                        cb_label = f'{var_verif_description} ({var_verif_units})', 
                        left_grid_label = False, 
                        right_grid_label = True, 
                        cmap = colormaps[var_verif]['map'], 
                        norm = colormaps[var_verif]['norm']
                    )
                    fig.savefig(
                        formatter.format_string(
                            "plot_orig", init_time=init_time, lead_time=lead_time.item()
                        ),
                        dpi=600,
                        bbox_inches='tight',
                        pad_inches=0.05
                    )
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
                    ds = build_dataset(
                        values=regridded_data, 
                        date=date_simus_ini + timedelta(hours=lead_time.item()), 
                        lat=obs_lat, 
                        lon=obs_lon, 
                        var_name=var_verif, 
                        attrs_var={'units': var_verif_units, 'long_name': var_verif_description}
                    )
                    ds.to_netcdf(
                        file_regrid,
                        encoding={'time': {'units': 'seconds since 1970-01-01'}}
                    )
                    print('... DONE')
        else:
            print(f"INFO: Valid times outside the lead times availables for init: {init_time}. Avoiding regrid")
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
