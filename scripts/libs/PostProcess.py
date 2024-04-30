import numpy as np

def KelvinToCelsius(tempK):
    print('INFO:PostProccess:convert Kelvin to Celsius')
    tempC = tempK - 273.15
    return tempC.copy()

def IrradianceToBrightnessTemperature(irradiance, v_c = 930.659 , A = 0.9983, B = 0.627):
    print('INFO:PostProccess:compute brightness temperature from irradiance values (channel 9)')
    # Parameters from http://eumetrain.org/data/2/204/204.pdf
    c_1 = 1.19104e-5
    c_2 = 1.43877
    
    term1 = ((c_1 * (v_c ** 3)) / irradiance) + 1
    term2 = np.log(term1)
    term3 = (c_2 * v_c / term2) - B
    btK = (term3 / A)
    btC = KelvinToCelsius(btK)
    return btC.copy()

def Reflectivity_dBZ(reflectivity):
    print('INFO:PostProccess:convert Reflectivity to dBZ units')
    newValues = 10.0 * np.log10(np.maximum(1.0, 200.0 * reflectivity**1.6))
    return newValues.copy()

def MetersToMilimeters(values_m):
    print('INFO:PostProccess:convert Meters to Milimeters')
    values_mm = values_m * 1000.0
    return values_mm.copy()

def compute_total_precipitation(list_precip):
    print('INFO:PostProccess:compute total precipitation from rain, graupel and snow')
    pcp = np.sum(list_precip, axis = 0)
    return pcp.copy()
