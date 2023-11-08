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

def make_dir_obs(obs_db, case):
    cwd = os.getcwd()
    os.chdir(f'../../OBSERVATIONS/')
    if os.path.exists(f'data_{obs_db}/') == False:
        os.mkdir(f'data_{obs_db}')
    os.chdir(f'data_{obs_db}/')
    if os.path.exists(f'{case}/') == False:
        os.mkdir(case)
    os.chdir(cwd)
    obs_path = f'../../OBSERVATIONS/data_{obs_db}/{case}/'
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
    
    obs_path = make_dir_obs(obs_db, case)

    #leemos las credenciales que nos permitiran acceder a los datos
    #estas credenciales las podeis leer de un archivo 'credenciales.json' o ponerlas en el script
    #keys = json.load(open('credenciales.json','r'))
    #consumer_key = keys['consumer_key']
    #consumer_secret = keys['consumer_secret']
    credentials = (consumer_key, consumer_secret)
    token = eumdac.AccessToken(credentials)
    print(f"This token {token} expires {token.expiration}")
    
    #Vamos a customizar el producto High Rate SEVIRI Level 1.5 Image Data - MSG - 0 degree
    #Seleccionamos por ejemplo el ultimo producto disponible
    datastore = eumdac.DataStore(token)
    datatailor = eumdac.DataTailor(token)
    selected_collection = datastore.get_collection('EO:EUM:DAT:MSG:HRSEVIRI')

    #latest = selected_collection.search().first()

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

        if str(product)[34:36] == "57":

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
        dataset.to_netcdf(datetime.strftime(date_process, f'{obs_path}{obs_filename}'), compute='True')
        os.remove(file)
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
