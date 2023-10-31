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

freqHours = 1

def main(obs, case, exp):
    # OBS data: database + variable
    obsDB, varRaw = obs.split('_')
    
    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H')

    # exp data
    dataExp = LoadConfigFileFromYaml(f'config/config_{exp}.yaml')
    model = dataExp['model']['name']

    # init times of nwp
    for init_time in dataExp['inits'].keys():
        date_exp_end = dataExp['inits'][init_time]['fcast_horiz']
    
        # set lead times from experiments
        date_simus_ini = datetime.strptime(init_time, '%Y%m%d%H')
        date_simus_end = datetime.strptime(date_exp_end, '%Y%m%d%H')
        if date_simus_ini < date_ini:
            forecast_ini = int((date_ini - date_simus_ini).total_seconds() / 3600.0)
        else:
            forecast_ini = 0
        forecast_horiz = int((date_simus_end - date_simus_ini).total_seconds() / 3600.0)
        if dataExp['vars'][varRaw]['accum'] == True:
            forecast_ini += 1
            forecast_horiz += 1
        print(f'Forecast from {exp}: {init_time}+{str(forecast_ini).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_ini), "%Y%m%d%H")}) up to {init_time}+{str(forecast_horiz).zfill(3)} ({datetime.strftime(date_simus_ini + timedelta(hours = forecast_horiz), "%Y%m%d%H")})')
        
        for forecast in range(forecast_ini, forecast_horiz + 1, freqHours):
            try:
                imagesRowBot = [Image.open(x) for x in [f'PLOTS/side_plots/plots_verif/FSS/{obs}/{case}/{exp}/FSS_{model}_{exp}_{obs}_{init_time}+{str(forecast).zfill(2)}.png', f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/SAL_{model}_{exp}_{obs}_{init_time}+{str(forecast).zfill(2)}.png', f'PLOTS/side_plots/plots_verif/SAL/{obs}/{case}/{exp}/DetectedObjects_{obs}_{exp}_{init_time}+{str(forecast).zfill(2)}.png']]
                imagesRowTop = [Image.open(x) for x in [f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{model}_{exp}_regrid_vs_{obs}_{init_time}+{str(forecast).zfill(2)}_pcolormesh.png', f'PLOTS/side_plots/plots_{obs}/{case}/{exp}/{model}_{exp}_orig_{init_time}+{str(forecast).zfill(2)}_pcolormesh.png']]

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

                new_im.save(f'PLOTS/side_plots/plots_verif/panels/{obs}/{case}/{exp}/panel_{model}_{exp}_{obs}_{init_time}+{str(forecast).zfill(2)}.png')
            except FileNotFoundError:
                pass
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
