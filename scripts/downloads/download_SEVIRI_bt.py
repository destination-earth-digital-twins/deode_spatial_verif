#!/usr/bin/env python
# coding: utf-8
#autores:  Lidia Escudero & Juan Jesús González-Alemán & Antonio Jiménez-Garrote

import os
import sys
sys.path.append('../libs/')
import eumdac
import shutil
import json
import fnmatch
import time
import glob
import numpy as np
from datetime import datetime, timedelta
from LoadWriteData import LoadConfigFileFromYaml, GetVarsFromNetCDF, GetLatLon2DfromNetCDF, BuildXarrayDataset
from PostProcess import IrradianceToBrightnessTemperature

obs = 'SEVIRI_bt'

def make_dir_obs(obs, case):
    cwd = os.getcwd()
    os.chdir(f'../../OBSERVATIONS/')
    if os.path.exists(f'data_{obs}/') == False:
        os.mkdir(f'data_{obs}')
    os.chdir(f'data_{obs}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
        print(f'INFO: ../../OBSERVATIONS/data_{obs}/{case}/ directory created')
    os.chdir(cwd)
    obs_path = f'../../OBSERVATIONS/data_{obs}/{case}/'
    return obs_path

def main(case, consumer_key, consumer_secret):
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')
    
    # observation database info
    config_obs_db = LoadConfigFileFromYaml(f'../../config/obs_db/config_{obs_db}.yaml')
    obs_filename = config_obs_db['format']['filename']
    obs_var_get = config_obs_db['vars'][var_verif]['var']

    # Case data: initial date + end date
    config_case = LoadConfigFileFromYaml(f'../../config/Case/config_{case}.yaml')
    date_ini = datetime.strptime(config_case['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(config_case['dates']['end'], '%Y%m%d%H')
    bounds_W, bounds_E, bounds_S, bounds_N = config_case['location']['NOzoom']
    
    obs_path = make_dir_obs(obs, case)
    
    credentials = (consumer_key, consumer_secret)
    token = eumdac.AccessToken(credentials)
    print(f"This token {token} expires {token.expiration}")
    
    datastore = eumdac.DataStore(token)
    datatailor = eumdac.DataTailor(token)
    selected_collection = datastore.get_collection('EO:EUM:DAT:MSG:HRSEVIRI')

    # Set sensing start and end time
    start = date_ini - timedelta(hours = 1)
    end = date_end
    print(start, end)

    # Retrieve datasets that match our filter
    products = selected_collection.search(dtstart=start,dtend=end)
    print(products)

    # Defining the chain configuration
    chain = eumdac.tailor_models.Chain(
        product='HRSEVIRI',
        format='netcdf4',
        filter={"bands" : ["channel_9"]},
        projection='geographic',
        roi={"NSWE": [bounds_N + 5, bounds_S - 5, bounds_W - 5, bounds_E + 5]}
    )

    print(chain)
    print(" ")
    for product in products:
        print("Date: {} {}z - Product: {}".format(str(product)[24:32],str(product)[32:36],product))
        date_product = datetime.strptime(str(product).split('-')[-2].split('.')[0], '%Y%m%d%H%M%S')
        file_to_find = datetime.strftime(date_product, f'{obs_path}{case}_SEVIRI_bt_%Y%m%d-%H%M_raw.nc')
        
        if ((str(product)[34:36] == "57") & (os.path.isfile(file_to_find) == False)):

            # Send the customisation to Data Tailor Web Services
            customisation = datatailor.new_customisation(product, chain)

            try:
                print(f"Customisation {customisation._id} started.")
            except eumdac.datatailor.DataTailorError as error:
                print(f"Error related to the Data Tailor: '{error.msg}'")
            except requests.exceptions.RequestException as error:
                print(f"Unexpected error: {error}")

            status = customisation.status
            sleep_time = 10 # seconds

            # Customisation Loop
            while status:
            # Get the status of the ongoing customisation
                status = customisation.status

                if "DONE" in status:
                    print(f"Customisation {customisation._id} is successfully completed.")
                    nc, = fnmatch.filter(customisation.outputs, '*.nc')

                    jobID= customisation._id

                    print(f"Dowloading the NETCDF4 output of the customisation {jobID}")
                    try:
                        with customisation.stream_output(nc,) as stream, \
                                open(stream.name, mode='wb') as fdst:
                            shutil.copyfileobj(stream, fdst)
                        print(f"Dowloaded the NETCDF4 output of the customisation {jobID}")
                        print(f"Downloaded the product {product}")

                        list_of_files = glob.glob('*') # * means all if need specific format then *.csv
                        latest_file = max(list_of_files, key=os.path.getctime)
                        print(f"File {latest_file} created")

                        # Absolute path of a file
                        new_name = "{}{}_SEVIRI_bt_{}-{}_raw.nc".format(obs_path,case,str(product)[24:32],str(product)[32:36])
                        # Renaming the file
                        os.rename(latest_file, new_name)
                        print(f"File {latest_file} moved to {new_name}")

                    except eumdac.datatailor.CustomisationError as error:
                        print(f"Data Tailor Error", error)
                    except requests.exceptions.RequestException as error:
                        print(f"Unexpected error: {error}")

                    break
                elif status in ["ERROR","FAILED","DELETED","KILLED","INACTIVE"]:
                    print(f"Customisation {customisation._id} was unsuccessful. Customisation log is printed.\n")
                    print(customisation.logfile)
                    break
                elif "QUEUED" in status:
                    print(f"Customisation {customisation._id} is queued.")
                elif "RUNNING" in status:
                    print(f"Customisation {customisation._id} is running.")
                time.sleep(sleep_time)
    
    # postprocess
    files_to_process = glob.glob(f'{obs_path}{case}_SEVIRI_bt_*raw.nc')
    files_to_process.sort()
    for file in files_to_process:
        date_raw = datetime.strptime(file, f'{obs_path}{case}_SEVIRI_bt_%Y%m%d-%H%M_raw.nc')
        date_process = date_raw + timedelta(minutes = 3)
        values_ir = GetVarsFromNetCDF(file, [obs_var_get,])
        values_bt = IrradianceToBrightnessTemperature(values_ir)
        lat2D, lon2D = GetLatLon2DfromNetCDF(file)
        dataset = BuildXarrayDataset(values_bt, lon2D, lat2D, date_process, varName = var_verif, descriptionNc = datetime.strftime(date_process, f'SEVIRI | Brightness Temperature - %Y%m%d%H'))
        file_new = datetime.strftime(date_process, f'{obs_path}{obs_filename}')
        print(f'INFO:saving processed values in {file_new}')
        dataset.to_netcdf(file_new, compute='True')
        print(f'INFO:removing {file}')
        os.remove(file)
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
