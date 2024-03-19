#!/usr/bin/env python
# coding: utf-8
"""
Based on https://stackoverflow.com/questions/30227466/combine-several-images-horizontally-with-python
"""

import sys
sys.path.append('scripts/libs/')
from datetime import datetime, timedelta
from PIL import Image
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
    is_accum = config_exp['vars'][var_verif]['accum']
    verif_at_0h = config_exp['vars'][var_verif]['verif_0h']

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
            try:
                imagesRowBot = [Image.open(x) for x in [f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSS_{exp_model}_{exp}_{obs}_{init_time}+{str(lead_time).zfill(2)}.png', f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SAL_{exp_model}_{exp}_{obs}_{init_time}+{str(lead_time).zfill(2)}.png', f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/DetectedObjects_{obs}_{exp}_{init_time}+{str(lead_time).zfill(2)}.png']]
                imagesRowTop = [Image.open(x) for x in [f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{exp_model}_{exp}_regrid_vs_{obs}_{init_time}+{str(lead_time).zfill(2)}_pcolormesh.png', f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{exp_model}_{exp}_orig_{init_time}+{str(lead_time).zfill(2)}_pcolormesh.png']]

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

                new_im.save(f'PLOTS/side_plots/plots_verif/panels/{obs}/{case}/{exp}/panel_{exp_model}_{exp}_{obs}_{init_time}+{str(lead_time).zfill(2)}.png')
            except FileNotFoundError:
                pass
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
