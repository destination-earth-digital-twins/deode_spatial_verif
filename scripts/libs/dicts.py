from LoadWriteData import get_vars_from_grib, get_lat_lon_from_grib, GetVarsFromNetCDF, GetLatLon2DfromNetCDF
from PostProcess import *
from colormaps import pcp_map, pcp_norm, bt_cmap, bt_norm, inverse_bt_cmap, inverse_bt_norm, refl_cmap, refl_norm

get_grid_function = {'Grib': get_lat_lon_from_grib, 'netCDF': GetLatLon2DfromNetCDF}
get_data_function = {'Grib': get_vars_from_grib, 'netCDF': GetVarsFromNetCDF}
colormaps = {'pcp': {'map': pcp_map, 'norm': pcp_norm}, 'bt': {'map': bt_cmap, 'norm': bt_norm}, 'inverse_bt': {'map': inverse_bt_cmap, 'norm': inverse_bt_norm}, 'refl': {'map': refl_cmap, 'norm': refl_norm}}
postprocess_function = {'K_C': KelvinToCelsius, 'IR_BT': IrradianceToBrightnessTemperature, 'Z_dBZ': Reflectivity_dBZ, 'm_mm': MetersToMilimeters, 'tp_deode': compute_total_precipitation}
