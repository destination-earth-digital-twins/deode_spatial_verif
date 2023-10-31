import numpy as np
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from colormaps import bt_cmap

rangesSAL = [(0, 0.1), (0.1, 0.2), (0.2, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 9999.999)]
colorsSAL = ['tab:green', 'tab:olive', 'gold', 'tab:orange', 'tab:red', 'black']

def PlotMapInAxis(ax, data, lat, lon, extent = [], titleLeft = '', titleRight = '', cbLabel = '', titleColorLeft = 'black', titleColorRight = 'black', xTopLabel = False, xBotLabel = True, yLeftLabel = True, yRightLabel = False, crs = ccrs.PlateCarree(), cmap = None, norm = None):
    if extent != []:
        ax.set_extent(extent, crs=crs)
    ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=0.75)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    
    if cmap is not None:
        cf = ax.pcolormesh(lon, lat, data, cmap=cmap, norm=norm, shading='auto')
    else:
        cf = ax.pcolormesh(lon, lat, data, shading='auto')
    
    # Add a color bar
    cb = plt.colorbar(cf, ax = ax, orientation='horizontal', aspect=70, shrink=.9, pad=0.1, extendrect='True')
    cb.set_label(cbLabel, size = 8)
    cb.ax.tick_params(labelsize = 8)
    if cmap == bt_cmap:
        cb.set_ticks([-80,-60,-40,-20,0,20,40])
    
    ax.set_title(titleLeft, loc='left', size = 8, color = titleColorLeft)
    ax.set_title(titleRight, loc='right', size = 8, color = titleColorRight)
    
    # Add the gridlines
    gl = ax.gridlines(crs=crs, draw_labels = True, linewidth=1, color='black', alpha=0.1, linestyle='dotted')
    gl.top_labels = xTopLabel # xlabels_top = False (deprecated)
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}
    gl.right_labels = yRightLabel
    gl.left_labels = yLeftLabel
    gl.bottom_labels = xBotLabel

def PlotBoundsInAxis(ax, bounds, text = '', color = 'tab:orange', projection = ccrs.PlateCarree()):
    lonMin, lonMax, latMin, latMax = bounds
    ax.plot([lonMin, lonMin], [latMax, latMin], color = color, linewidth = 1, transform = projection)
    ax.plot([lonMin, lonMax], [latMin, latMin], color = color, linewidth = 1, transform = projection)
    ax.plot([lonMax, lonMax], [latMin, latMax], color = color, linewidth = 1, transform = projection)
    ax.plot([lonMax, lonMin], [latMax, latMax], color = color, linewidth = 1, transform = projection)
    ax.text(lonMin - 0.1, latMax + 0.1, text, color = color, fontsize = 8, transform = projection)

def PlotContourDomainInAxis(ax, lat2D, lon2D, text = '', color = 'tab:blue', projection = ccrs.PlateCarree()):
    ax.plot(lon2D[:, 0], lat2D[:, 0], color = color, linewidth = 1, transform = projection)
    ax.plot(lon2D[0, :], lat2D[0, :], color = color, linewidth = 1, transform = projection)
    ax.plot(lon2D[:, -1], lat2D[:, -1], color = color, linewidth = 1, transform = projection)
    ax.plot(lon2D[-1, :], lat2D[-1, :], color = color, linewidth = 1, transform = projection)
    ax.text(lon2D[0, 0] - 0.1, lat2D[-1, 0] + 0.1, text, color = color, fontsize = 8, transform = projection)
    
def PlotFSSInAxis(ax, data, cmap = 'Blues', title = '', xLabel = '', yLabel = ''):
    sns.heatmap(data, cmap = cmap, annot = True, linewidths = .5, ax = ax, cbar = False)
    ax.set_xlabel(xLabel, fontweight = "bold", fontsize = 8)
    ax.set_ylabel(yLabel, fontweight = "bold", fontsize = 8)
    ax.set_title(title, loc = 'left', fontsize = 8)
    ax.tick_params(axis='both', labelsize=8)

def PlotViolinInAxis(ax, data, title = '', xLabel = '', yLabel = '', yLim = [0, 1]):
    sns.violinplot(data=data, palette="pastel", bw=0.2, cut=0, linewidth=2, ax = ax)
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
        
def PlotSALinAxis(ax, structures, amplitudes, locations, ranges = rangesSAL, colors = colorsSAL, title = '', plotLegend = True):
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

    ax.set_title(title, loc='left', fontsize=8)
    ax.set_xlabel('Structure (S)', fontsize=8)
    ax.set_ylabel('Amplitude (A)', fontsize=8)
    ax.set_xticks(np.arange(-2, 2.5, 0.5))
    ax.tick_params(axis='both', labelsize=8, direction = 'in')
