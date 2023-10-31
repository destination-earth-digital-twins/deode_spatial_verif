"""
Creo que deberian cambiar las lineas 355-360 de pysteps.verification.salscores.
Se machaca la variable tstorm_kwargs haciendo inutil este argumento al inicio del SAL.
- Eso pensaba pero si usas la funcion _sal_detect_objects con argumento tstorm_kwargs != None, tiene prioridad sobre los thr_*. NO SE POR QUE !!!

PROPONGO: sustituir  "tstorm_kwargs = {" por "tstorm_kwargs.update({" y las sucesivas actualizaciones: "minmax": threshold, etc. 
Esto se puede meter en una funcion sencilla de forma que las lineas 350-360 serían:
    if thr_factor is not None:
        tstorm_kwargs = _update_tstorm_kwargs(precip, thr_factor, thr_quantile, tstorm_kwargs)
Como añadido a esta libreria introduciria una funcion que printe los objetos, tanto el dataframe como el plot.
"""
import numpy as np
import pandas as pd
from pysteps.verification import salscores
from pysteps.feature import tstorm as tstorm_detect
from skimage.measure import regionprops_table
from scipy.ndimage import center_of_mass
from math import sqrt
from matplotlib import pyplot as plt

REGIONPROPS = [
    "label",
    "weighted_centroid",
    "max_intensity",
    "intensity_image",
]

def SAL(prediction_raw, observation_raw, thr_factor = 0.067, thr_quantile = 0.95, tstorm_kwargs = None, verbose = False, cmap = None, norm = None, figname = 'verbose.png'): 
    prediction = np.copy(prediction_raw)
    observation = np.copy(observation_raw)
    prediction[prediction < 0.0] = 0.0
    observation[observation < 0.0] = 0.0
    
    prediction_with_nan = np.copy(prediction_raw)
    observation_with_nan = np.copy(observation_raw)
    prediction_with_nan[prediction_with_nan < 0.0] = np.nan
    observation_with_nan[observation_with_nan < 0.0] = np.nan    
    
    
    if verbose == True:
        observation_objects, observation_params = _sal_detect_objects_custom(observation, thr_factor, thr_quantile, tstorm_kwargs)
        prediction_objects, prediction_params = _sal_detect_objects_custom(prediction, thr_factor, thr_quantile, tstorm_kwargs)
        print(f'observation objects for structure: {observation_objects}')
        print(f'prediction objects for structure: {prediction_objects}')
        maxRows = max(len(observation_objects), len(prediction_objects))
        if maxRows > 0:
            fig_height = 1.0 + 2.0 * float(maxRows)
            fig = plt.figure(figsize = (5.0 / 2.54, fig_height / 2.54), clear = True)
            iteratorAxis = 0
            for iteratorCol, df, axis_title in zip(range(2), [observation_objects, prediction_objects], ['OBS', 'PRED']):
                iteratorRow = 0
                for detected_object in df['intensity_image'].values:
                    ax = fig.add_subplot(maxRows, 2, iteratorRow * 2 + iteratorCol + 1)
                    if ((cmap != None) & (norm != None)):
                        ax.imshow(np.flipud(detected_object), cmap = cmap, norm = norm)
                    else:
                        ax.imshow(np.flipud(detected_object))
                    if iteratorRow == 0:
                        ax.set_title(axis_title, fontsize = 4, fontweight = 'bold')
                    ax.set_xticks([])
                    ax.set_yticks([])
                    iteratorRow += 1
            fig.subplots_adjust(top=(1.0 - 1.2 / fig_height))
            fig.suptitle(f" OBS: max_num_features: {observation_params['max_num_features']}; minref: {np.round(observation_params['minref'], 2)}; maxref: {np.round(observation_params['maxref'], 2)};\n  mindiff: {observation_params['mindiff']}; minsize: {observation_params['minsize']}; minmax: {np.round(observation_params['minmax'], 2)}; mindis: {observation_params['mindis']}\n PRED: max_num_features: {prediction_params['max_num_features']}; minref: {np.round(prediction_params['minref'], 2)}; maxref: {np.round(prediction_params['maxref'], 2)}\n mindiff: {prediction_params['mindiff']}; minsize: {prediction_params['minsize']}; minmax: {np.round(prediction_params['minmax'], 2)}; mindis: {prediction_params['mindis']}\n", fontsize = 4)
            fig.savefig(figname, dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
    
    structure = sal_structure_custom(prediction, observation, thr_factor, thr_quantile, tstorm_kwargs)
    amplitude = salscores.sal_amplitude(prediction_with_nan, observation_with_nan)
    location = sal_location_custom(prediction, observation, thr_factor, thr_quantile, tstorm_kwargs)
    return structure, amplitude, location

def sal_structure_custom(prediction, observation, thr_factor, thr_quantile, tstorm_kwargs):
    prediction_objects, prediction_params = _sal_detect_objects_custom(
        prediction, thr_factor, thr_quantile, tstorm_kwargs
    )
    observation_objects, observation_params = _sal_detect_objects_custom(
        observation, thr_factor, thr_quantile, tstorm_kwargs
    )
    prediction_volume = salscores._sal_scaled_volume(prediction_objects).sum()
    observation_volume = salscores._sal_scaled_volume(observation_objects).sum()
    nom = prediction_volume - observation_volume
    denom = prediction_volume + observation_volume
    return np.divide(nom, (0.5 * denom))

def _sal_detect_objects_custom(precip, thr_factor, thr_quantile, tstorm_kwargs):
    '''
    if not PANDAS_IMPORTED:
        raise MissingOptionalDependency(
            "The pandas package is required for the SAL "
            "verification method but it is not installed"
        )
    if not SKIMAGE_IMPORTED:
        raise MissingOptionalDependency(
            "The scikit-image package is required for the SAL "
            "verification method but it is not installed"
        )
    '''
    if thr_factor is not None and thr_quantile is None:
        raise ValueError("You must pass thr_quantile, too")
    if tstorm_kwargs is None:
        tstorm_kwargs = dict()
    if thr_factor is not None:
        tstorm_kwargs = _update_tstorm_kwargs(precip, thr_factor, thr_quantile, tstorm_kwargs)
    _, labels = tstorm_detect.detection(precip, **tstorm_kwargs)
    labels = labels.astype(int)
    precip_objects = regionprops_table(
        labels, intensity_image=precip, properties=REGIONPROPS
    )
    return pd.DataFrame(precip_objects), tstorm_kwargs

def _update_tstorm_kwargs(precip, thr_factor, thr_quantile, tstorm_kwargs):
    update_tstorm = dict(tstorm_kwargs)
    zero_value = np.nanmin(precip)
    threshold = thr_factor * np.nanquantile(
        precip[precip > zero_value], thr_quantile
    )
    update_tstorm.update({"minmax": threshold, "maxref": threshold + 1e-5, "mindiff": 1e-5, "minref": threshold})
    return update_tstorm

def sal_location_custom(prediction, observation, thr_factor, thr_quantile, tstorm_kwargs):
    return salscores._sal_l1_param(prediction, observation) + _sal_l2_param_custom(
        prediction, observation, thr_factor, thr_quantile, tstorm_kwargs
    )

def _sal_l2_param_custom(prediction, observation, thr_factor, thr_quantile, tstorm_kwargs):
    maximum_distance = sqrt(
        ((observation.shape[0]) ** 2) + ((observation.shape[1]) ** 2)
    )
    obs_r = _sal_weighted_distance_custom(observation, thr_factor, thr_quantile, tstorm_kwargs)
    forc_r = _sal_weighted_distance_custom(prediction, thr_factor, thr_quantile, tstorm_kwargs)

    location_2 = 2 * ((abs(obs_r - forc_r)) / maximum_distance)
    return float(location_2)

def _sal_weighted_distance_custom(precip, thr_factor, thr_quantile, tstorm_kwargs):
    '''
    if not PANDAS_IMPORTED:
        raise MissingOptionalDependency(
            "The pandas package is required for the SAL "
            "verification method but it is not installed"
        )
    '''
    precip_objects, precip_params = _sal_detect_objects_custom(
        precip, thr_factor, thr_quantile, tstorm_kwargs
    )
    if len(precip_objects) == 0:
        return np.nan
    centroid_total = center_of_mass(np.nan_to_num(precip))
    r = []
    for i in precip_objects.label - 1:
        xd = (precip_objects["weighted_centroid-1"][i] - centroid_total[1]) ** 2
        yd = (precip_objects["weighted_centroid-0"][i] - centroid_total[0]) ** 2

        dst = sqrt(xd + yd)
        sumr = (precip_objects.intensity_image[i].sum()) * dst

        sump = precip_objects.intensity_image[i].sum()

        r.append({"sum_dist": sumr, "sum_p": sump})
    rr = pd.DataFrame(r)
    return rr.sum_dist.sum() / (rr.sum_p.sum())
