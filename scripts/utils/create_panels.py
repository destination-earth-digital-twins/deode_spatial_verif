#!/usr/bin/env python
# coding: utf-8
"""
Based on https://stackoverflow.com/questions/30227466/combine-several-images-horizontally-with-python
"""

import os
import sys
from datetime import datetime, timedelta
from PIL import Image

sys.path.append('scripts/libs/')
from namingformatter import NamingFormatter
from LoadWriteData import LoadConfigFileFromYaml
from times import set_lead_times


def main(obs, case, exp, relative_indexed_path):
    print("INFO: RUNNING CREATE PANELS")
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')

    # observation database info
    print("INFO: Loading OBS YAML file: config/obs_db/config_{obs_db}.yaml")
    config_obs_db = LoadConfigFileFromYaml(
        f'config/obs_db/config_{obs_db}.yaml'
    )
    accum_h = config_obs_db["vars"][var_verif]["verif"]["times"]["accum_hours"]
    freq_verif = config_obs_db["vars"][var_verif]["verif"]["times"]["freq_verif"]
    print(
        f"INFO: Loaded config file for {obs_db} database:\n "
        f"verification time arguments: acc. values: {accum_h} h; "
        f"freq. verif.: {freq_verif} h"
    )
    
    # Case data: initial date + end date
    print(f"INFO: Loading CASE YAML file: config/Case/config_{case}.yaml")
    config_case = LoadConfigFileFromYaml(f'config/Case/{relative_indexed_path}/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    print(
        f"INFO: Loaded config file for {case} case study:\n "
        f'init: {config_case["dates"]["ini"]}; '
        f'end: {config_case["dates"]["end"]}'
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
        f"model: {exp_model};\n var. to get: {var_verif}"
    )

    # naming formatter
    formatter = NamingFormatter(obs, case, exp, relative_indexed_path)

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
            
            for lead_time in lead_times:
                file_plot_regrid = formatter.format_string(
                    template="plot_regrid",
                    init_time=init_time,
                    lead_time=lead_time.item(),
                    acc_h=accum_h
                )
                if os.path.isfile(file_plot_regrid):
                    imagesRowBot = []
                    file_plot_orig = formatter.format_string(
                        template="plot_orig",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    file_plot_fss = formatter.format_string(
                        template="plot_fss",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    file_plot_sal = formatter.format_string(
                        template="plot_sal",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    file_plot_objects = formatter.format_string(
                        template="plot_objects",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    for x in [file_plot_fss, file_plot_sal, file_plot_objects]:
                        try:
                            imagesRowBot.append(Image.open(x))
                        except FileNotFoundError:
                            print(f"INFO: File '{x}' not found")
                    imagesRowTop = [Image.open(x) for x in [file_plot_regrid, file_plot_orig]]
        
                    widthsRowBot, heightsRowBot = zip(*(i.size for i in imagesRowBot))
                    widthsRowTop, heightsRowTop = zip(*(i.size for i in imagesRowTop))
        
                    max_width = max(sum(widthsRowBot), sum(widthsRowTop))
                    max_height = max(sum([heightsRowBot[0], max(heightsRowTop)]), sum([heightsRowBot[-1], max(heightsRowTop)]))
        
                    new_im = Image.new('RGB', (max_width, max_height))
        
                    x_offset, y_offset = 0, 0
                    for imBot in imagesRowTop:
                        new_im.paste(imBot, (x_offset,y_offset))
                        x_offset += imBot.size[0]
        
                    x_offset, y_offset = 0, min(heightsRowTop)
                    for imTop in imagesRowBot:
                        new_im.paste(imTop, (x_offset,y_offset))
                        x_offset += imTop.size[0]

                    figname = formatter.format_string(
                        template="plot_panel",
                        init_time=init_time,
                        lead_time=lead_time.item(),
                        acc_h=accum_h
                    )
                    new_im.save(
                        figname
                    )
                    print(f"INFO: Panel '{figname}' created")
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3],  sys.argv[4])
