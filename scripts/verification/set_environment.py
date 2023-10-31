#!/usr/bin/env python
# coding: utf-8

import os, sys
sys.path.append('scripts/libs/')
from LoadWriteData import LoadConfigFileFromYaml

def main(obs, case, exp):
    # current work directory
    cwd = os.getcwd()

    # exp data
    dataExp = LoadConfigFileFromYaml(f'config/config_{exp}.yaml')
    
    # OBSERVATIONS
    os.chdir(f'{cwd}/OBSERVATIONS/')
    if os.path.exists(f'data_{obs}/') == False:
        os.mkdir(f'data_{obs}')
    os.chdir(f'data_{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    
    # SIMULATIONS
    os.chdir(f'{cwd}/SIMULATIONS/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)
    os.chdir(f'{exp}/')
    if os.path.exists('data_orig/') == False:
        os.mkdir('data_orig')
    os.chdir('data_orig/')
    for init_time in dataExp['inits'].keys():
        if os.path.exists(f'{init_time}/') == False:
            os.mkdir(init_time)
    os.chdir(f'{cwd}/SIMULATIONS/{exp}/')
    if os.path.exists('data_regrid/') == False:
        os.mkdir('data_regrid')
    os.chdir('data_regrid/')
    for init_time in dataExp['inits'].keys():
        if os.path.exists(f'{init_time}/') == False:
            os.mkdir(init_time)
    
    # PLOTS
    os.chdir(f'{cwd}/PLOTS/main_plots/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    
    os.chdir(f'{cwd}/PLOTS/side_plots/')
    if os.path.exists(f'plots_{obs}/') == False:
        os.mkdir(f'plots_{obs}')
    os.chdir(f'plots_{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(f'{case}/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/FSS/')
    if os.path.exists(f'{obs}/') == False:
        os.mkdir(obs)
    os.chdir(f'{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(f'{case}/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/SAL/')
    if os.path.exists(f'{obs}/') == False:
        os.mkdir(obs)
    os.chdir(f'{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(f'{case}/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/panels/')
    if os.path.exists(f'{obs}/') == False:
        os.mkdir(obs)
    os.chdir(f'{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(f'{case}/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)
    os.chdir(f'{cwd}/PLOTS/side_plots/plots_verif/gif_frames/')
    if os.path.exists(f'{obs}/') == False:
        os.mkdir(obs)
    os.chdir(f'{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)

    # pickles
    os.chdir(f'{cwd}/pickles/FSS')
    if os.path.exists(f'{obs}/') == False:
        os.mkdir(obs)
    os.chdir(f'{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(f'{case}/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)
    os.chdir(f'{cwd}/pickles/SAL/')
    if os.path.exists(f'{obs}/') == False:
        os.mkdir(obs)
    os.chdir(f'{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(f'{case}/')
    if os.path.exists(f'{exp}/') == False:
        os.mkdir(exp)

    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
