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
#consumer_key = 'N8yf6pY67pQgKqmomfg_fp0TiQka'
#consumer_secret = 'KfaDikgM7GmolJfhLb09xnQF0bsa'

def main(case, consumer_key, consumer_secret):
    # OBS data: database + variable
    obsDB, var = obs.split('_')
    
    # observation database info
    dataObs = LoadConfigFileFromYaml(f'../../config/config_{obsDB}.yaml')
    obsFileName = dataObs['format']['filename']
    varGet = dataObs['vars'][var]['var']

    # Case data: initial date + end date
    dataCase = LoadConfigFileFromYaml(f'../../config/config_{case}.yaml')
    date_ini = datetime.strptime(dataCase['dates']['ini'], '%Y%m%d%H')
    date_end = datetime.strptime(dataCase['dates']['end'], '%Y%m%d%H')
    bounds_W, bounds_E, bounds_S, bounds_N = dataCase['location']['NOzoom']
    
    dir=f'../../OBSERVATIONS/data_{obs}/{case}/'
    
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
        #roi={"NSWE": [47,28,5,30]} #IANOS
    )
    # roi parameter above is a pre-defined one. It's possible to use "roi=" as follows "{"NSWE" : [37,2,-19,21]}".

    print(chain)
    print(" ")
    for product in products:
        #print(product)
        #print(str(product)[24:30])
        print("Date: {} {}z - Product: {}".format(str(product)[24:32],str(product)[32:36],product))

        if str(product)[34:36] == "57":
        #if str(product)[32:36] == "1457":

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
                        #new_name = "{}/HRSEVIRI_{}_{}T{}z.nc".format(dir,channel_name,str(product)[24:32],str(product)[32:36])
                        new_name = "{}/{}_SEVIRI_bt_{}-{}.nc".format(dir,case,str(product)[24:32],str(product)[32:36])
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
    filesToProcess = glob.glob(f'{dir}{case}_SEVIRI_bt_*.nc')
    filesToProcess.sort()
    for file in filesToProcess:
        dateOrig = datetime.strptime(file, f'{dir}{case}_SEVIRI_bt_%Y%m%d-%H%M.nc')
        dateProcess = dateOrig + timedelta(minutes = 3)
        dataIR = GetVarsFromNetCDF(file, [varGet])
        dataBt = IrradianceToBrightnessTemperature(dataIR)
        lat2D, lon2D = GetLatLon2DfromNetCDF(file)
        dataset = BuildXarrayDataset(dataBt, lon2D, lat2D, dateProcess, varName = var, descriptionNc = datetime.strftime(dateProcess, f'SEVIRI | Brightness Temperature - %Y%m%d%H'))
        dataset.to_netcdf(datetime.strftime(dateProcess, f'{dir}SEVIRI_bt_%Y%m%d-%H%M.nc'), compute='True')
        os.system(f'mv {file} ../../../databases/{obsDB}/')
    return 0

if __name__ == '__main__':
    main(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))
