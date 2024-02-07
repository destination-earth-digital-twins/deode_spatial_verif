from LoadWriteData import GetVarsFromGrib, GetLatLon2DFromGrib, GetVarsFromNetCDF, GetLatLon2DfromNetCDF, get_vars_from_deode, get_latlon_from_deode
from PostProcess import *
from colormaps import pcp_map, pcp_norm, bt_cmap, bt_norm, inverse_bt_cmap, inverse_bt_norm, refl_cmap, refl_norm

get_grid_function = {'Grib': GetLatLon2DFromGrib, 'netCDF': GetLatLon2DfromNetCDF, 'Grib2': get_latlon_from_deode}
get_data_function = {'Grib': GetVarsFromGrib, 'netCDF': GetVarsFromNetCDF, 'Grib2': get_vars_from_deode}
colormaps = {'pcp': {'map': pcp_map, 'norm': pcp_norm}, 'bt': {'map': bt_cmap, 'norm': bt_norm}, 'inverse_bt': {'map': inverse_bt_cmap, 'norm': inverse_bt_norm}, 'refl': {'map': refl_cmap, 'norm': refl_norm}}
postprocess_function = {'K_C': KelvinToCelsius, 'IR_BT': IrradianceToBrightnessTemperature, 'Z_dBZ': Reflectivity_dBZ, 'm_mm': MetersToMilimeters}
