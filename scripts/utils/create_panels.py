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


def main(obs, case, exp):
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')
    
    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')

    # exp data
    config_exp = LoadConfigFileFromYaml(f'config/exp/config_{exp}.yaml')
    exp_model = config_exp['model']['name']
    exp_model_in_filename = exp_model.replace(' ', '').replace('.', '-')
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']

    # naming formatter
    formatter = NamingFormatter(obs, case, exp)

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
        
        for lead_time in lead_times:
            file_plot_regrid = formatter.format_string(
                "plot_regrid",
                init_time=init_time,
                lead_time=lead_time.item()
            )
            if os.path.isfile(file_plot_regrid):
                imagesRowBot = []
                file_plot_orig = formatter.format_string(
                    "plot_orig", init_time=init_time, lead_time=lead_time.item()
                )
                file_plot_fss = formatter.format_string(
                    "plot_fss", init_time=init_time, lead_time=lead_time.item()
                )
                file_plot_sal = formatter.format_string(
                    "plot_sal", init_time=init_time, lead_time=lead_time.item()
                )
                file_plot_objects = formatter.format_string(
                    "plot_objects",
                    init_time=init_time,
                    lead_time=lead_time.item()
                )
                for x in [file_plot_fss, file_plot_sal, file_plot_objects]:
                    try:
                        imagesRowBot.append(Image.open(x))
                    except FileNotFoundError:
                        pass
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
    
                new_im.save(
                    formatter.format_string(
                        "plot_panel",
                        init_time=init_time,
                        lead_time=lead_time.item()
                    )
                )
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
