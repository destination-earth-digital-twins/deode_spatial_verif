import numpy as np
from datetime import datetime

def set_domain_verif(valid_time, verif_domains):
    if verif_domains == None:
        verif_domain = None
    else:
        dates_verif = np.array([datetime.strptime(date, '%Y%m%d%H') for date in verif_domains.keys()])
        try:
            date_domain_verif = dates_verif[dates_verif <= valid_time][-1]
            verif_domain = verif_domains[date_domain_verif.strftime('%Y%m%d%H')]
        except IndexError:
            verif_domain = None
    return verif_domain

def CropDomainsFromBounds(data, lat2D, lon2D, bounds):
    lonMin, lonMax, latMin, latMax = bounds
    ids = np.argwhere((lat2D >= latMin) & (lat2D <= latMax) & (lon2D >= lonMin) & (lon2D <= lonMax))
    idLatIni, idLatEnd, idLonIni, idLonEnd = ids[:,0].min(), ids[:,0].max() + 1, ids[:,1].min(), ids[:,1].max() + 1
    return data[idLatIni:idLatEnd, idLonIni:idLonEnd].copy()
