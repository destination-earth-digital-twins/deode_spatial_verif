import os
import pandas as pd
from datetime import datetime
import sys

sys.path.append("scripts/libs/")
from miscelanea import check_is_empty_dir
from LoadWriteData import LoadConfigFileFromYaml


def main(obs, case):
    print("INFO: RUNNING LINK OBS")
    # OBS data: database + variable
    obs_db, var_verif = obs.split("_")

    # observation database info
    config_obs_db = LoadConfigFileFromYaml(
        f"config/obs_db/config_{obs_db}.yaml"
    )
    obs_path = config_obs_db["path"]
    obs_filename = config_obs_db["format"]["filename"][var_verif]
    print(
        f"INFO: Load config file for {obs_db} database: \n "
        + f"obs downloaded at: {obs_path}; file format: {obs_filename}"
    )

    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f"config/Case/config_{case}.yaml")
    date_ini = datetime.strptime(config_case["dates"]["ini"], "%Y%m%d%H")
    date_end = datetime.strptime(config_case["dates"]["end"], "%Y%m%d%H")
    print(
        f"INFO: Load config file for {case} case study: \n "
        + f"init: {config_case['dates']['ini']}; "
        + f"end: {config_case['dates']['end']}"
    )

    dates = pd.date_range(date_ini, date_end, freq="1h").to_pydatetime()
    for date in dates:
        obs_destin = date.strftime(
            f"OBSERVATIONS/data_{obs}/{case}/{obs_filename}"
        )
        if not os.path.isfile(obs_destin):
            obs_origin = date.strftime(os.path.join(obs_path, obs_filename))
            if os.path.isfile(obs_origin):
                os.system(f"ln -s {obs_origin} {obs_destin}")
                print(f"INFO: link {obs_destin} --> {obs_origin} created")
            else:
                print(f"INFO: file {obs_origin} not downloaded")
        else:
            print(f"INFO: file {obs_destin} exists")


if __name__ == "__main__":
    main(str(sys.argv[1]), str(sys.argv[2]))
