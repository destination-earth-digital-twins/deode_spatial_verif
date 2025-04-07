#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append('scripts/libs/')
from LoadWriteData import LoadConfigFileFromYaml
from pathlib import Path

def main(obs, case, exp, relative_indexed_path):
    # current work directory
    cwd = os.getcwd()

    # exp data
    config_path = Path(f"config/exp/{relative_indexed_path}/config_{exp}.yaml")
    if not config_path.exists():
     raise FileNotFoundError(f"config_{exp}.yaml not found at {config_path}")
    dataExp = LoadConfigFileFromYaml(str(config_path))
    
    # OBSERVATIONS
    os.chdir(f'{cwd}/OBSERVATIONS/')
    os.makedirs(f'data_{obs}', exist_ok=True)
    os.chdir(f'data_{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    
    # SIMULATIONS
    os.chdir(f'{cwd}/SIMULATIONS/')
    os.makedirs(f'{relative_indexed_path}/{exp}', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{exp}/')

    os.makedirs('data_orig', exist_ok=True)
    os.chdir('data_orig/')
    for init_time in dataExp['inits'].keys():
            os.makedirs(init_time, exist_ok=True)
    os.chdir(f'{cwd}/SIMULATIONS/{relative_indexed_path}/{exp}/')
    os.makedirs('data_regrid', exist_ok=True)
    os.chdir('data_regrid/')
    for init_time in dataExp['inits'].keys():
            os.makedirs(init_time, exist_ok=True)
    
    # PLOTS
    os.chdir(f'{cwd}/PLOTS/main_plots/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{cwd}/PLOTS/side_plots/')
    os.makedirs(f'plots_{obs}', exist_ok=True)
    os.chdir(f'plots_{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{case}/')
    os.makedirs(f'{exp}/', exist_ok=True)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/FSS/')
    os.makedirs(obs, exist_ok=True)
    os.chdir(f'{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{case}/')
    os.makedirs(f'{exp}/', exist_ok=True)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/SAL/')
    os.makedirs(f'{obs}', exist_ok=True)
    os.chdir(f'{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{case}/')
    os.makedirs(f'{exp}/', exist_ok=True)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/panels/')
    os.makedirs(f'{obs}', exist_ok=True)
    os.chdir(f'{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{case}/')
    os.makedirs(f'{exp}', exist_ok=True)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/gif_frames/')
    os.makedirs(f'{obs}/', exist_ok=True)
    os.chdir(f'{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)

    # pickles
    os.chdir(f'{cwd}/pickles/FSS')
    os.makedirs(f'{obs}', exist_ok=True)
    os.chdir(f'{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{case}/')
    os.makedirs(f'{exp}', exist_ok=True)
    os.chdir(f'{cwd}/pickles/SAL/')
    os.makedirs(f'{obs}', exist_ok=True)
    os.chdir(f'{obs}/')
    os.makedirs(f'{relative_indexed_path}/{case}/', exist_ok=True)
    os.chdir(f'{relative_indexed_path}/{case}/')
    os.makedirs(f'{exp}/', exist_ok=True)

    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
