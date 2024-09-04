from LoadWriteData import get_vars_from_grib, get_lat_lon_from_grib, get_vars_from_nc, get_lat_lon_from_nc
from PostProcess import *
from colormaps import pcp_map, pcp_norm, bt_cmap, bt_norm, inverse_bt_cmap, inverse_bt_norm, refl_cmap, refl_norm, ecmwf_pcp_cmap, ecmwf_pcp_norm

get_grid_function = {'Grib': get_lat_lon_from_grib, 'netCDF': get_lat_lon_from_nc}
get_data_function = {'Grib': get_vars_from_grib, 'netCDF': get_vars_from_nc}
colormaps = {'pcp': {'map': ecmwf_pcp_cmap, 'norm': ecmwf_pcp_norm}, 'rain': {'map': ecmwf_pcp_cmap, 'norm': ecmwf_pcp_norm}, 'bt': {'map': bt_cmap, 'norm': bt_norm}, 'inverse_bt': {'map': inverse_bt_cmap, 'norm': inverse_bt_norm}, 'refl': {'map': refl_cmap, 'norm': refl_norm}}
postprocess_function = {'K_C': KelvinToCelsius, 'IR_BT': IrradianceToBrightnessTemperature, 'Z_dBZ': Reflectivity_dBZ, 'm_mm': MetersToMilimeters, 'tp_deode': compute_total_precipitation}
