import sys
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

sys.path.append("scripts/libs/")
from miscelanea import check_is_empty_dir
from LoadWriteData import LoadConfigFileFromYaml, build_dataset
from dicts import get_data_function, get_grid_function


def main(obs, case):
    print("INFO: RUNNING LINK OBS")
    # OBS data: database + variable
    obs_db, var_verif = obs.split("_")

    # observation database info
    print(f"INFO: Loading OBS YAML file: config/obs_db/config_{obs_db}.yaml")
    config_obs_db = LoadConfigFileFromYaml(
        f"config/obs_db/config_{obs_db}.yaml"
    )
    obs_path = config_obs_db["path"]
    obs_path_destin = f"OBSERVATIONS/data_{obs}/{case}"
    obs_filename = config_obs_db["format"]["filename"][var_verif]
    obs_fileformat = config_obs_db['format']['fileformat']
    if config_obs_db['vars'][var_verif]['postprocess']:
        obs_var_get = var_verif
    else:
        obs_var_get = config_obs_db['vars'][var_verif]['var']
    var_verif_description = config_obs_db['vars'][var_verif]['description']
    var_verif_units = config_obs_db['vars'][var_verif]['units']
    accum_h = config_obs_db["vars"][var_verif]["verif"]["times"]["accum_hours"]
    freq_verif = config_obs_db["vars"][var_verif]["verif"]["times"]["freq_verif"]
    print(
        f"INFO: Loaded config file for {obs_db} database:\n "
        + f"obs downloaded at: {obs_path};\n file name: {obs_filename};\n "
        + f"file format: {obs_fileformat};\n "
        + f"hours between verif timesteps: {freq_verif};\n "
        + f"values accumulated in {accum_h} hours (0: inst.)"
    )

    # Case data: initial date + end date
    print(f"INFO: Loading CASE YAML file: config/Case/config_{case}.yaml")
    config_case = LoadConfigFileFromYaml(f"config/Case/config_{case}.yaml")
    date_ini = datetime.strptime(config_case["dates"]["ini"], "%Y%m%d%H")
    date_end = datetime.strptime(config_case["dates"]["end"], "%Y%m%d%H")
    print(
        f"INFO: Loaded config file for {case} case study: \n "
        + f"init: {config_case['dates']['ini']}; "
        + f"end: {config_case['dates']['end']}"
    )

    # dates to verify
    dates_to_verif = pd.date_range(
        date_ini,
        date_end,
        freq=f"{freq_verif}h"
    ).to_pydatetime()
    for date_verif in dates_to_verif:
        # dates of each accumulation period
        # assume that each obs file contains hourly acc. values
        files_acc = []
        date_prev = date_verif - timedelta(hours=accum_h - 1)
        dates = pd.date_range(date_prev, date_verif, freq="1h").to_pydatetime()
        for date in dates:
            # link files
            obs_destin = date.strftime(
                os.path.join(obs_path_destin, obs_filename)
            )
            if not os.path.isfile(obs_destin):
                obs_origin = date.strftime(os.path.join(obs_path, obs_filename))
                if os.path.isfile(obs_origin):
                    os.system(f"ln -s {obs_origin} {obs_destin}")
                    print(f"INFO: link {obs_destin} --> {obs_origin} created")
                    files_acc.append(obs_destin)
                else:
                    print(f"INFO: file {obs_origin} not downloaded")
            else:
                print(f"INFO: file {obs_destin} exists")
                files_acc.append(obs_destin)
        # compute accumulations
        file_accum = date_verif.strftime(
            os.path.join(
                obs_path_destin,
                f"acc{accum_h}h_{'.'.join(obs_filename.split('.')[:-1])}.nc"
            )
        )
        if (
            not os.path.isfile(file_accum)
            and accum_h > 1
            and len(files_acc) == accum_h
        ):
            print(
                "INFO: computing accumulated values: "
                f"{datetime.strftime(date_prev - timedelta(hours=1), '%Y%m%d%H')}"
                f" - {date_verif.strftime('%Y%m%d%H')}"
            )
            values_all = []
            obs_lat, obs_lon = get_grid_function[obs_fileformat](files_acc[0])
            for obs_file in files_acc:
                values_file = get_data_function[obs_fileformat](obs_file, obs_var_get)
                values_all.append(values_file)
            acc_values = np.sum(values_all, axis=0)

            # save file
            ds = build_dataset(
                values=acc_values,
                date=date_verif,
                lat=obs_lat,
                lon=obs_lon,
                var_name=obs_var_get,
                attrs_var={
                    'units': var_verif_units,
                    'long_name': var_verif_description.replace("1-hour", f"{accum_h}-hour")
                }
            )
            ds.to_netcdf(
                file_accum,
                encoding={'time': {'units': 'seconds since 1970-01-01'}}
            )
            print(f"INFO: file '{file_accum}' saved")

    if check_is_empty_dir(os.path.join(obs_path_destin, "*")):
        raise ValueError(f"Error: '{obs_path_destin}' está vacío.")


if __name__ == "__main__":
    main(str(sys.argv[1]), str(sys.argv[2]))
