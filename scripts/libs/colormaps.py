import numpy as np
from matplotlib.colors import from_levels_and_colors, ListedColormap, BoundaryNorm

clevs_bt = np.arange(-90,41,1)
bt_c = np.array([[127, 0,    127],
                 [138, 11,   133],
                 [149, 22,   140],
                 [160, 33,   146],
                 [171, 44,   152],
                 [182, 56,   159],
                 [193, 67,   165],
                 [204, 78,   171],
                 [215, 89,   177],
                 [226, 100,  184],
                 [237, 111,  190],
                 [200, 200,  200],
                 [180, 180,  180],
                 [160, 160,  160],
                 [140, 140,  140],
                 [120, 120,  120],
                 [100, 100,  100],
                 [80, 80,     80],
                 [60, 60,     60],
                 [40, 40,     40],
                 [20, 20,     20],
                 [0, 0,        0],
                 [26, 0,       0],
                 [51, 0,       0],
                 [77, 0,       0],
                 [102, 0,      0],
                 [128, 0,      0],
                 [153, 0,      0],
                 [179, 0,      0],
                 [204, 0,      0],
                 [230, 0,      0],
                 [255, 0,      0],
                 [255, 26,     5],
                 [255, 51,    10],
                 [255, 77,    15],
                 [255, 102,   20],
                 [255, 128,   25],
                 [255, 153,   30],
                 [255, 179,   35],
                 [255, 204,   40],
                 [255, 230,   45],
                 [255, 255,   50],
                 [235, 255,   50],
                 [214, 255,   50],
                 [194, 255,   50],
                 [173, 255,   50],
                 [153, 255,   50],
                 [132, 255,   50],
                 [112, 255,   50],
                 [91, 255,    50],
                 [71, 255,    50],
                 [50, 255,    50],
                 [45, 230,    58],
                 [40, 204,    65],
                 [35, 179,    73],
                 [30, 153,    81],
                 [25, 128,    89],
                 [20, 102,    96],
                 [15, 77,    104],
                 [10, 51,    112],
                 [5, 26,     119],
                 [0, 0,      127],
                 [6, 28,     141],
                 [11, 57,    155],
                 [17, 85,    170],
                 [22, 113,   184],
                 [28, 142,   198],
                 [33, 170,   212],
                 [39, 198,   227],
                 [44, 227,   241],
                 [50, 255,   255],
                 [255, 255,  255],
                 [251, 251,  251],
                 [247, 247,  247],
                 [242, 242,  242],
                 [238, 238,  238],
                 [234, 234,  234],
                 [230, 230,  230],
                 [226, 226,  226],
                 [222, 222,  222],
                 [217, 217,  217],
                 [213, 213,  213],
                 [209, 209,  209],
                 [205, 205,  205],
                 [201, 201,  201],
                 [196, 196,  196],
                 [192, 192,  192],
                 [188, 188,  188],
                 [184, 184,  184],
                 [180, 180,  180],
                 [176, 176,  176],
                 [171, 171,  171],
                 [167, 167,  167],
                 [163, 163,  163],
                 [159, 159,  159],
                 [155, 155,  155],
                 [150, 150,  150],
                 [146, 146,  146],
                 [142, 142,  142],
                 [138, 138,  138],
                 [134, 134,  134],
                 [130, 130,  130],
                 [125, 125,  125],
                 [121, 121,  121],
                 [117, 117,  117],
                 [113, 113,  113],
                 [109, 109,  109],
                 [105, 105,  105],
                 [100, 100,  100],
                 [96, 96,     96],
                 [92, 92,     92],
                 [88, 88,     88],
                 [84, 84,     84],
                 [79, 79,     79],
                 [75, 75,     75],
                 [71, 71,     71],
                 [67, 67,     67],
                 [63, 63,     63],
                 [59, 59,     59],
                 [54, 54,     54],
                 [50, 50,     50],
                 [46, 46,     46],
                 [42, 42,     42],
                 [38, 38,     38],
                 [33, 33,     33],
                 [29, 29,     29],
                 [25, 25,     25],
                 [21, 21,     21],
                 [17, 17,     17],
                 [13, 13,     13],
                 [8, 8,        8],
                 [4, 4,        4]], np.float32) / 255.0

bt_cmap, bt_norm = from_levels_and_colors(clevs_bt, bt_c,extend="both")
inverse_bt_cmap, inverse_bt_norm = from_levels_and_colors(-1.0 * np.flipud(clevs_bt), np.flipud(bt_c),extend="both")

pcp_clevs=[0.,0.5,1,2,3,4,5,10,15,20,30,50,75,100,125]
accum2 = np.array([[255,255,255],
                    [209,229,240], 
                    [146,197,222],
                    [67,147,195], 
                    [33,102,172],
                    [5,48,97], 
                    [0,104,55],
                    [65,171,93], 
                    [255,227,145],
                    [254,178,76], 
                    [253,141,60],
                    [252,78,42],
                    [227,26,28],
                    [128,0,38],
                    [129,15,124]], np.float32) / 255.0
 
pcp_map, pcp_norm = from_levels_and_colors(pcp_clevs, accum2,
                                           extend="max")

# Define the five HEX colors
color1 = '#fdfdfd'
color2 = '#9d55be'
color3 = '#f700fb'
color4 = '#bd0004'
color5 = '#d60000'

color6 = '#f90203'
color7 = '#fd9500'
color8 = '#e3bf00'
color9 = '#fdf902'
color10 = '#028d03'

color11 = '#00c502'
color12 = '#03fa00'
color13 = '#0300f2'
color14 = '#02a2fb'
color15 = '#02ebe9'

# Convert the HEX codes to RGB values as floats between 0 and 1
rgb1 = tuple(int(color1[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb2 = tuple(int(color2[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb3 = tuple(int(color3[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb4 = tuple(int(color4[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb5 = tuple(int(color5[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb6 = tuple(int(color6[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb7 = tuple(int(color7[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb8 = tuple(int(color8[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb9 = tuple(int(color9[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb10 = tuple(int(color10[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb11 = tuple(int(color11[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb12 = tuple(int(color12[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb13 = tuple(int(color13[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb14 = tuple(int(color14[i:i+2], 16) / 255 for i in (1, 3, 5))
rgb15 = tuple(int(color15[i:i+2], 16) / 255 for i in (1, 3, 5))

refl_colors = ['white', rgb15, rgb14, rgb13, rgb12, rgb11, rgb10, rgb9, rgb8, rgb7, rgb6, rgb5, rgb4, rgb3, rgb2, rgb1]
refl_cmap = ListedColormap(refl_colors)
refl_cmap.set_under('0.75')
refl_clevs = [-8889000.0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
refl_norm = BoundaryNorm(refl_clevs, refl_cmap.N)

ecmwf_accum_pcp_levels = [0.5, 2, 5, 10, 20, 30, 40, 50, 60, 80, 100, 125, 150, 200, 300, 500]
ecmwf_accum_pcp_colors = [(0.75, 0.95, 0.93), (0.45, 0.93, 0.78), (0.06999, 0.85, 0.61), (0.53, 0.8, 0.13),
           (0.6, 0.91, 0.05699), (0.9, 1, 0.4), (0.89, 0.89, 0.066), (1, 0.73, 0.003906),
           (1, 0.49, 0.003906), 'red', (0.85, 0.003906, 1), (0.63, 0.007294, 0.92),
           (0.37, 0.29, 0.91), (0.03999, 0.03999, 0.84), (0.04199, 0.04199, 0.43),
           (0.45, 0.45, 0.45)]
ecmwf_accum_pcp_cmap, ecmwf_accum_pcp_norm = from_levels_and_colors(ecmwf_accum_pcp_levels, ecmwf_accum_pcp_colors, extend = 'max')

# add white for values between 0.0 - 0.5
ecmwf_accum_pcp_levels.insert(0, 0.)
ecmwf_accum_pcp_colors.insert(0, "white")
ecmwf_accum_pcp_cmap_2, ecmwf_accum_pcp_norm_2 = from_levels_and_colors(
    ecmwf_accum_pcp_levels,
    ecmwf_accum_pcp_colors,
    extend = 'max'
)

ecmw_pcp_levels = [0,0.1,0.25,0.5,1,1.5,2,2.5,3,4,5,6,8,10,12,20,40]
ecmw_pcp_colors = [
    'white',
    (0.75,0.95,0.93),
    (0.45,0.93,0.78),
    (0.06999,0.85,0.61),
    (0.53,0.8,0.13),
    (0.6,0.91,0.05699),
    (0.9,1,0.4),
    (0.89,0.89,0.066),
    (1,0.73,0.003906),
    (1,0.49,0.003906),
    'red',
    (0.85,0.003906,1),
    (0.63,0.007294,0.92),
    (0.37,0.29,0.91),
    (0.03999,0.03999,0.84),
    (0.04199,0.04199,0.43),
    (0.45,0.45,0.45)]
ecmwf_pcp_cmap, ecmwf_pcp_norm = from_levels_and_colors(ecmw_pcp_levels, ecmw_pcp_colors, extend = 'max')

ecmwf_wind_gust_levels = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,50]
ecmwf_wind_gust_colors = [
    (0.6,0.9,1),
    (0.45,0.7,1),
    (0.3,0.5,1),
    (0.15,0.3,1),
    (0.8,1,0.2),
    (0.65,0.95,0),
    (0.5,0.85,0),
    (0.15,0.75,0.1),
    (0,0.55,0.19),
    (1,0.85,0),
    (1,0.74,0),
    (1,0.62,0),
    (1,0.5,0),
    (0.85,0.45,0),
    (1,0.75,0.75),
    (1,0.5,0.5),
    (1,0,0),
    (0.8,0,0),
    (0.6,0,0),
    (0.85,0.6,1),
    (0.75,0.4,1),
    (0.6,0.2,1),
    (0.5,0,0.9),
    (0.35,0,0.6)]
ecmwf_wind_gust_cmap, ecmwf_wind_gust_norm = from_levels_and_colors(ecmwf_wind_gust_levels, ecmwf_wind_gust_colors, extend = 'max')

flash_levels = [0., 0.5, 1., 1.5, 3.5, 7., 15., 25., 50.]
flash_colors_rgb = [
    (255, 255, 255),
    (212, 212, 212),
    (126, 126, 126),
    (190, 190,   0),
    (255, 255,   0),
    (255, 169,   0),
    (255,  83,   0),
    (169,   0,   0),
    (40,   0,   0)
]
flash_colors = []
for rgb in flash_colors_rgb:
    flash_colors.append([v / 255. for v in rgb])
flash_cmap, flash_norm = from_levels_and_colors(flash_levels, flash_colors, extend="max")
