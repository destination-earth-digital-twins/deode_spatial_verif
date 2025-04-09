import sys
import numpy as np
import pandas as pd
import seaborn as sns
from glob import glob
from scipy.stats import wilcoxon
from matplotlib import pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.lines import Line2D

sys.path.append('scripts/libs/')
from LoadWriteData import LoadConfigFileFromYaml, LoadPickle
from plots import plot_fss_scores, plot_sal, plot_violin

def sorted_list_files(string):
    list_files = glob(string)
    list_files.sort()
    return list_files

def main(obs, case, exps, relative_indexed_path):
    # OBS data: database + variable
    obs_db, var_verif = obs.split('_')

    # observation database info
    print("INFO: Loading OBS YAML file: config/obs_db/config_{obs_db}.yaml")
    config_obs_db = LoadConfigFileFromYaml(
        f'config/obs_db/config_{obs_db}.yaml'
    )
    accum_h = config_obs_db["vars"][var_verif]["verif"]["times"]["accum_hours"]
    print(
        f"INFO: Loaded config file for {obs_db} database:\n "
        f"verification time argument: acc. values: {accum_h} h; "
    )

    # Experiments to compare between
    expLowRes, expHighRes = exps.split('-VS-')
    model_name = {}
    
    # Load results for FSS and SAL
    fss, sal = {}, {}
    for dictionary, stat in zip((fss, sal), ('FSS', 'SAL')):
        for exp in (expLowRes, expHighRes):
            config_exp = LoadConfigFileFromYaml(f'config/exp/{relative_indexed_path}/config_{exp}.yaml')
            print(f"INFO: Loaded config file for {exp} simulation")
            dictionary[exp] = {}
            model_name[exp] = config_exp['model']['name']
            for init_time in config_exp['inits'].keys():
                file_pickl = f"pickles/{stat}/{obs}/{relative_indexed_path}/{case}/{exp}/{stat}_{model_name[exp].replace(' ', '').replace('.', '-')}_{exp}_{obs}_acc{accum_h}h_{init_time}.pkl"
                try:
                    dictionary[exp][init_time] = LoadPickle(file_pickl)
                    print(f"INFO: pickle '{file_pickl}' loaded")
                except FileNotFoundError:
                    print(f"INFO: pickle '{file_pickl}' not found.")

    # common inits & lead times from FSS pickles
    mask_isin = np.isin(list(fss[expLowRes].keys()), list(fss[expHighRes].keys()))
    common_inits = np.array(list(fss[expLowRes].keys()))[mask_isin].copy()
    common_lead_times = {}
    for init_time in common_inits:
        mask_isin = np.isin(list(fss[expLowRes][init_time].keys()), list(fss[expHighRes][init_time].keys()))
        common_lead_times[init_time] = np.array(list(fss[expLowRes][init_time].keys()))[mask_isin]
        print(
            f"INFO: common lead times:\n {init_time}:\n "
            f"{common_lead_times[init_time]}"
        )

    try:
        # get thresholds and scales from FSS
        namecols_fss = fss[expLowRes][common_inits[0]][common_lead_times[common_inits[0]][0]].columns
        namerows_fss = fss[expLowRes][common_inits[0]][common_lead_times[common_inits[0]][0]].index
    except IndexError:
        raise ValueError(f"INFO: no common verifications lead times for case '{case}' and '{exps}'")

    # figure FSS mean
    fig = plt.figure(figsize = (19. / 2.54, 9. / 2.54), clear = True)
    for iterator, exp, label in zip(range(2), (expLowRes, expHighRes), ("Threshold", "")):
        fss_scores = []
        for init_time in common_inits:
            for lead_time in common_lead_times[init_time]:
                fss_scores.append(fss[exp][init_time][lead_time].values.copy())
        ax = fig.add_subplot(1, 2, iterator + 1)
        ax = plot_fss_scores(
            ax=ax,
            data=pd.DataFrame(
                np.nanmean(fss_scores, axis=0),
                columns=namecols_fss,
                index=namerows_fss
            ),
            title=f'{model_name[exp]} [exp: {exp}]',
            x_label="Scale",
            y_label=label
        )
        if iterator > 0:
            ax.tick_params(axis = 'y', length = 0.0, labelleft = False)
    fig.suptitle(f"FSS plot | mean values | OBS: {obs}", fontsize=8)
    fig.savefig(
        f"PLOTS/main_plots/{relative_indexed_path}/{case}/Comparison_FSSmean_{obs}_acc{accum_h}h_{exps.replace('-VS-', '_vs_')}.png",
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.05
    )
    plt.close()
    
    # figure FSS distribution
    with sns.axes_style('whitegrid'):
        fig = plt.figure(figsize=(19.0 / 2.54, 14.0 / 2.54), clear = True)
        # fig.subplots_adjust(wspace = 0.45, hspace = 0.3)
        for iterator_row, namerow in enumerate(namerows_fss.values):
            for iterator_col, namecol in enumerate(namecols_fss.values):
                fss_exps_fixed_thresh_scale = {}
                for exp in (expLowRes, expHighRes):
                    values = []
                    index = []
                    for init_time in common_inits:
                        for lead_time in common_lead_times[init_time]:
                            values.append(fss[exp][init_time][lead_time].loc[namerow, namecol])
                            index.append(f'{init_time}+{lead_time}')
                    fss_exps_fixed_thresh_scale[exp] = pd.DataFrame(values, columns = [namecol], index = pd.Index(index))
                fss_comp_exps = pd.merge(fss_exps_fixed_thresh_scale[expLowRes], fss_exps_fixed_thresh_scale[expHighRes], left_index = True, right_index = True) # double check with common inits and lead times
                fss_comp_exps.rename(columns = {f'{namecol}_x': expLowRes, f'{namecol}_y': expHighRes}, inplace = True)
                
                ax = fig.add_subplot(len(namerows_fss), len(namecols_fss), iterator_row * len(namecols_fss) + iterator_col + 1)
                ax.set_yticks(np.arange(0.0, 1.25, 0.25))
                if ((iterator_col == 0) & (iterator_row == (len(namerows_fss) - 1))):
                    ax = plot_violin(ax, fss_comp_exps, x_label = namecol, y_label = namerow)
                elif iterator_col == 0:
                    ax = plot_violin(ax, fss_comp_exps, y_label = namerow)
                elif iterator_row == (len(namerows_fss) - 1):
                    ax = plot_violin(ax, fss_comp_exps, x_label = namecol)
                    ax.set_yticklabels([])
                else:
                    ax = plot_violin(ax, fss_comp_exps)
                    ax.set_yticklabels([])
                ax.tick_params(axis = 'x', length = 0.0, labelbottom = False)
                # if two data series are (not) statisticaly different --> green (red) contour
                try:
                    pValue = wilcoxon(fss_comp_exps.dropna()[expLowRes].values, fss_comp_exps.dropna()[expHighRes].values)[1] # pValue only allows two data series
                except ValueError:
                    pValue = None
                if pValue is not None:
                    print(f'{namerow} - {namecol} pValue: {pValue}')
                    if pValue < 0.05:
                        for index in (0, 1):
                            try:
                                ax.collections[index].set_edgecolor('tab:green')
                            except IndexError:
                                pass
        fig.suptitle(
            f'FSS distributions | OBS: {obs}\n{expLowRes} (left) - {expHighRes} (right)',
            fontsize=8
        )
        fig.supxlabel("Scales", fontsize=8, fontweight="bold")
        fig.supylabel("Thresholds", fontsize=8, fontweight="bold")
        fig.savefig(f"PLOTS/main_plots/{relative_indexed_path}/{case}/Comparison_FSSdist_{obs}_acc{accum_h}h_{exps.replace('-VS-', '_vs_')}.png", dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)
        plt.close()
    
    # figure SAL all
    with sns.axes_style('darkgrid'):
        fig = plt.figure(figsize = (18. / 2.54, 8. / 2.54), clear = True)
        for iterator, exp in zip(range(2), (expLowRes, expHighRes)):
            ax = fig.add_subplot(1, 2, iterator + 1)
            sal_all_lead_times = pd.DataFrame()
            for init_time in common_inits:
                sal_all_lead_times = pd.concat([sal_all_lead_times.copy(), sal[exp][init_time]['values'].loc[common_lead_times[init_time]].copy()])
            if iterator == 1:
                bool_legend = True
                dict_params = {key: sal[exp][init_time]['detect_params'][key] for key in ('f', 'q', 'minsize', 'mindis')}
            else:
                bool_legend = False
                dict_params = {}
            _ = plot_sal(
                ax=ax,
                structures=sal_all_lead_times.dropna()['Structure'].values,
                amplitudes=sal_all_lead_times.dropna()['Amplitude'].values,
                locations=sal_all_lead_times.dropna()['Location'].values,
                title=f'{model_name[exp]} [exp: {exp}]',
                detect_params=dict_params,
                plot_legend=bool_legend
            )
        fig.suptitle(f"SAL plot | OBS: {obs}", fontsize=8)
        fig.savefig(f"PLOTS/main_plots/{relative_indexed_path}/{case}/Comparison_SALall_{obs}_acc{accum_h}h_{exps.replace('-VS-', '_vs_')}.png", dpi = 600, bbox_inches = 'tight', pad_inches = 0.05)   
        plt.close()
    return 0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
