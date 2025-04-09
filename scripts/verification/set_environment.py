#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append('scripts/libs/')
from LoadWriteData import LoadConfigFileFromYaml
from pathlib import Path

def main(obs, case, exp, relative_indexed_path):
    print("INFO: RUNNING SET ENVIRONMENT")
    # current work directory
    cwd = os.getcwd()

    # exp data
    config_exp = f"config/exp/{relative_indexed_path}/config_{exp}.yaml"
    print("INFO: Loading EXP YAML file: {config_exp}")
    if not os.path.isfile(config_exp):
        raise FileNotFoundError(f"ERROR: {config_exp} not found")
    data_exp = LoadConfigFileFromYaml(config_exp)
    inits_exp = list(data_exp['inits'].keys())
    print(
        f"INFO: Loaded config file for {exp} simulation:\n "
        f"inits available: {inits_exp}"
    )

    # OBSERVATIONS
    os.makedirs(
        f"{cwd}/OBSERVATIONS/data_{obs}/{relative_indexed_path}/{case}/",
        exist_ok=True
    )
    
    # SIMULATIONS
    for init_time in inits_exp:
        for key in ("orig", "regrid"):
            os.makedirs(
                f"{cwd}/SIMULATIONS/{relative_indexed_path}/{exp}/data_{key}/{init_time}",
                exist_ok=True
            )

    # PLOTS
    os.makedirs(
        f"{cwd}/PLOTS/main_plots/{relative_indexed_path}/{case}/",
        exist_ok=True
    )
    os.makedirs(
        f"{cwd}/PLOTS/side_plots/plots_{obs}/{relative_indexed_path}/{case}/{exp}",
        exist_ok=True
    )
    for key in ("FSS", "SAL", "panels"):
        os.makedirs(
            f"{cwd}/PLOTS/side_plots/plots_verif/{key}/{obs}/{relative_indexed_path}/{case}/{exp}",
            exist_ok=True
        )
    os.makedirs(
        f"{cwd}/PLOTS/side_plots/plots_verif/gif_frames/{obs}/{relative_indexed_path}/{case}",
        exist_ok=True
    )

    # pickles
    for key in ("FSS", "SAL"):
        os.makedirs(
            f"{cwd}/pickles/{key}/{obs}/{relative_indexed_path}/{case}/{exp}",
            exist_ok=True
        )

    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
