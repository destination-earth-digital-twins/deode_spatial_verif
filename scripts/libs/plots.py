import math
import numpy as np
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
from colormaps import bt_cmap
from domains import CropDomainsFromBounds

rangesSAL = [(0, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 9999.999)]
colorsSAL = ['tab:green', 'tab:olive', 'gold', 'tab:orange', 'tab:red', 'black']

def has_decimals(value):
    dec_part, int_part = math.modf(value)
    return dec_part != 0.0

def map_formatter(ax, extent = [], title = '', font_size = 8, top_grid_label = False, bot_grid_label = True, left_grid_label = True, right_grid_label = False):
    if title != '':
        ax.set_title(title, size = font_size)
    if extent != []:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth = 1)
    ax.add_feature(cfeature.BORDERS, linewidth = 0.5)
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    gl = ax.gridlines(crs = ccrs.PlateCarree(), draw_labels = True, x_inline = False, y_inline = False, alpha = 0.4)
    gl.xlabel_style = {'size': font_size, 'rotation': 0}
    gl.ylabel_style = {'size': font_size}
    gl.top_labels = top_grid_label
    gl.bottom_labels = bot_grid_label
    gl.left_labels = left_grid_label
    gl.right_labels = right_grid_label
    return ax

def plot_domain_in_axis(ax, lat, lon, color = 'black', linewidth = 0.75):
    for idx in (0, -1):
        ax.plot(lon[:, idx], lat[:, idx], color = color, linewidth = linewidth, transform = ccrs.PlateCarree())
        ax.plot(lon[idx, :], lat[idx, :], color = color, linewidth = linewidth, transform = ccrs.PlateCarree())
    return ax

def PlotMapInAxis(ax, data, lat, lon, extent = [], title = '', cb_label = '', font_size = 8, draw_bnds = False, top_grid_label = False, bot_grid_label = True, left_grid_label = True, right_grid_label = False, cmap = None, norm = None):
    ax = map_formatter(
        ax = ax, 
        extent = extent, 
        title = title, 
        font_size = font_size, 
        top_grid_label = top_grid_label, 
        bot_grid_label = bot_grid_label, 
        left_grid_label = left_grid_label, 
        right_grid_label = right_grid_label
    )
    
    if cmap is not None and norm is not None:
        cf = ax.pcolormesh(lon, lat, data, cmap = cmap, norm = norm, transform = ccrs.PlateCarree())
    else:
        cf = ax.pcolormesh(lon, lat, data)
    
    cb = plt.colorbar(
        cf, 
        ax = ax, 
        orientation = 'horizontal', 
        aspect = 25, 
        pad = 0.1, 
        format = FuncFormatter(lambda x, _: f'{x:.1f}' if has_decimals(x) else f'{x:.0f}')#((abs(x) < 1) & (abs(x) > 0)) else f'{x:.0f}')
    )
    cb.set_label(cb_label, size = 8)
    cb.ax.tick_params(labelsize = 8)
    if cmap == bt_cmap:
        cb.set_ticks([-80, -60, -40, -20, 0, 20, 40])
    elif cmap is not None:
        cb.set_ticks(norm.boundaries)
    else:
        pass
    
    if draw_bnds:
        ax = plot_domain_in_axis(ax, lat, lon)
    
    return ax, cb

def plot_verif_domain_in_axis(ax, verif_domain, lat, lon, color = 'black', linewidth = 0.75):
    lat_crop = CropDomainsFromBounds(lat, lat, lon, verif_domain)
    lon_crop = CropDomainsFromBounds(lon, lat, lon, verif_domain)
    ax = plot_domain_in_axis(ax, lat_crop, lon_crop, color, linewidth)
    return ax
    
def PlotFSSInAxis(ax, data, cmap = 'Blues', title = '', xLabel = '', yLabel = ''):
    sns.heatmap(data, cmap = cmap, annot = True, linewidths = .5, ax = ax, cbar = False)
    ax.set_xlabel(xLabel, fontweight = "bold", fontsize = 8)
    ax.set_ylabel(yLabel, fontweight = "bold", fontsize = 8)
    ax.set_title(title, loc = 'left', fontsize = 8)
    ax.tick_params(axis='both', labelsize=8)

def PlotViolinInAxis(ax, data, title = '', xLabel = '', yLabel = '', yLim = [0, 1]):
    sns.violinplot(data=data, palette="pastel", cut=0, linewidth=2, ax = ax)
    ax.set_ylim(yLim)
    ax.set_ylabel(yLabel, fontweight="bold",fontsize = 8)
    ax.tick_params(axis='both', labelsize=8)
    if xLabel != '':
        ax.set_xlabel(xLabel, fontweight="bold",fontsize = 8)
    sns.despine(left=True, bottom=True)
    if title != '':
        ax.set_title(title, loc='center', fontsize=8)#, pad=15)

def SetColorToLocationValue(location, ranges, colors):
    for idx, interval in enumerate(ranges):
        vmin, vmax = interval
        if ((location >= vmin) & (location < vmax)):
            color = colors[idx]
    return color
        
def PlotSALinAxis(ax, structures, amplitudes, locations, ranges = rangesSAL, colors = colorsSAL, title = '', detect_parms = {}, plotLegend = True):
    try:
        colorsLocation = [SetColorToLocationValue(locValue, ranges, colors) for locValue in locations]
    except:
        colorsLocation = [SetColorToLocationValue(locValue, ranges, colors) for locValue in (locations,)]
    ax.scatter(structures, amplitudes, c = colorsLocation, zorder = 4)
    
    if len(colorsLocation) > 1:
        #compute mean and interquartile range
        p25_S, p50_S, p75_S = np.percentile(structures, [25, 50, 75])
        p25_A, p50_A, p75_A = np.percentile(amplitudes, [25, 50, 75])
        ax.add_patch(Rectangle((p25_S, p25_A), p75_S - p25_S, p75_A - p25_A, alpha = 0.25, color='tab:blue', zorder = 5))
        ax.axvline(x = p50_S, color = 'tab:blue', linestyle = '--', linewidth = 0.5, zorder = 5)
        ax.axhline(y = p50_A, color = 'tab:blue', linestyle = '--', linewidth = 0.5, zorder = 5)
    
    ax.set_xlim([-2.005, 2.005])
    ax.set_ylim([-2.005, 2.005])
    ax.axhline(y = 0, color = 'grey')
    ax.axvline(x = 0, color = 'grey')
    ax.axvline(x = 2, color = 'grey')
    ax.axhline(y = 2, color = 'grey')
    ax.axvline(x = -2, color = 'grey')
    ax.axhline(y = -2, color = 'grey')

    legend_handles = [Line2D([], [], marker = '.', color = color, linestyle = 'None') for color in colors]
    legend_labels = [f'[{vmin}, {vmax})' for vmin, vmax in ranges]
    legend_labels[-1] = f'= {ranges[-1][0]}'
    if plotLegend == True:
        ax.legend(handles = legend_handles, labels=legend_labels, bbox_to_anchor= (1.0, 0.5), loc= "center left", title='Location (L)', title_fontsize = 8, fontsize=8)

    if detect_parms != {}:
        text = '\n'.join([f'{k}: {v}' for k,v in detect_parms.items()])
        ax.text(1.05, 0.15, text, va='center', ha='left', fontsize=6, transform=ax.transAxes)

    ax.set_title(title, loc='left', fontsize=8)
    ax.set_xlabel('Structure (S)', fontsize=8)
    ax.set_ylabel('Amplitude (A)', fontsize=8)
    ax.set_xticks(np.arange(-2, 2.5, 0.5))
    ax.tick_params(axis='both', labelsize=8, direction = 'in')

def plot_detected_objects(observation_objects, prediction_objects, cmap = None, norm = None):
    maxRows = max(len(observation_objects), len(prediction_objects))
    fig_height = 1.0 + 2.0 * float(maxRows)
    fig = plt.figure(figsize = (5.0 / 2.54, fig_height / 2.54), clear = True)
    if maxRows > 0:
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
    # fig.subplots_adjust(top=(1.0 - 0.9 / fig_height))
    fig.suptitle(f"Detected objects", fontsize = 8, fontweight = 'bold')
    return fig
