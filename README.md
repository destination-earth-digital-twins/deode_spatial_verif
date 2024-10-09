Documentation
=============

***Spatial verification tool***

**Legend:**

\(i\) *OBS*: combination of the database name of the observations (\<obs_db\>) along with the variable to be verified (\<var_verif\>) joined with the character \"\_\", e.g. SEVIRI_bt, IMERG_pcp, OPERA_rain. 

\(ii\) *Case*: name of the extreme event to be verified. It is recommended to use the same case study name as in [dcmdb](https://github.com/destination-earth-digital-twins/dcmdb) database, if it exists there, although for the moment the connection between dcmdb and deode_spatial_verif has not been done.

\(iii\) *exp*: name of the experiment to be verified, e.g. AIB_46h1_de2, VAL500m_46h1_de2. Again, it is recommended to use the same experiment name as in dcmdb.

# Configs

The templates of these files are located in the config/templates/ folder. Modified configuration files should be placed in the corresponding subdirectory in config/. The **parameters to be configured** in order to perform the spatial verification are detailed in this section. This setup is divided into 3 types of configuration files:

## Observation config file: config\_\<obs_db\>.yaml

-   path. 
    -   **path**. \[str\]. Directory where the observations are ready to be used during the verification exercise. If they have not been previously downloaded and formatted, the value of this parameter may remain empty. See [first step of main scripts](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#main-scripts) for further details.

-   format. Name and extension of the files to be used as observations for spatial verification. The format of the files may not match the originals. This is due to the necessity for some databases to be processed before use. For instance, SEVIRI provides irradiance values from channel 9. Since post-processing of the raw data is required to convert to brightness temperature, the raw data are processed and saved in netCDF format for simplicity.

    -   **filename**. \[str\]. Name of the observation file with extension, if any. It must contain the required characters to indicate the date format used by datetime.

    -   **fileformat**. \[str\]. File format of the observation file. Possible values are: netCDF, Grib.

-   vars. Information regarding the variable to be used for verification.

    -   **\<var_verif\>**. \[str\]. Variable name to be verified. Possible values are: pcp (precipitation), bt (brightness temperature), rain (rainfall), refl (maximum reflectivity).

        -   **var_raw**. \[str\]. Variable name to get from the raw files.

        -   **postprocess**. \[bool\]. Boolean value. It indicates whether the raw files of the observations have been processed or not. This control parameter is used to tell the verification process which variable to get: \'var\' or \<var_verif\>.

        -   **res**. \[str\]. Spatial resolution of the observations. IMPORTANT: there must be a single space between value and unit.

        -   **description**. \[str\]. Description of \<var_verif\>. Used as a colorbar label in plots.

        -   **units**. \[str\]. Units of \<var_verif\>.

        -   FSS. Threshold and scales for FSS.

            -   **thresholds**. \[list\]. List of the different thresholds (float values) to be verified in FSS.

            -   **scales**. \[list\]. List of the different scales (int values) to be verified in FSS. Numbers relate to pixels, not length units.

        -   SAL. Parameters to be used in SAL. These parameters are only used for object detection, which is required to compute structure and location values.

            -   **f**. \[float\]. Multiplicative factor to apply in the SAL methodology following (Wernli et al., 2008). The value they set is 1/15.

            -   **q**. \[float\]. Quartile of the observations/experiments to be estimated to set an object detection threshold. A value of 0.95 is recommended to avoid outliers (Gilleland et al., 2009).

            -   **tstorm_kwargs**. \[dict\]. Additional object detection parameters. See [tstorm](https://github.com/pySTEPS/pysteps/blob/master/pysteps/feature/tstorm.py) for further details.

## Case config file: config\_\<Case\>.yaml

-   dates. Time period where the extreme event occurs.

    -   **ini**. \[str\]. Time (UTC) at which the event starts in the format \"%Y%m%d%H\".

    -   **end**. \[str\]. Time (UTC) at which the event ends in the format \"%Y%m%d%H\".

-   location. Spatial domain covered by the extreme event.

    -   **NOzoom**. \[list\]. List of plotting domain coordinates \[\<lon_min\>, \<lon_max\>, \<lat_min\>, \<lat_max\>\].

-   verif_domain. A sequence of verification domains to be used as a common domain for the spatial verification of the experiments. If at the initial timestep where the event starts (see [\"dates\": \"ini\"](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#case-config-file-config_caseyaml)) there is no verification domain defined, a cropping of the domain of the experiment to be verified is performed. This is not recommended since it does not ensure a common verification domain between different experiments of a common case. The sequence of different verification domains at different time instants allows the tracking of a moving event. The [Ianos medicane](https://github.com/DEODE-NWP/DE330.5.3.2_Deliverable_annexes/blob/main/Ianos_Medicane_DTOD_spatial_verification.pdf) is an example.

    -   **\<%Y%m%d%H\>(\[str\])**. \[list\] List of verification domain coordinates \[\<lon_min\>, \<lon_max\>, \<lat_min\>, \<lat_max\>\].

## Experiment config file: config\_\<exp\>.yaml

-   model.

    -   **name**. \[str\]. Model name. Used for generated file names and plot titles.

-   format. Name and extension of the files to be used as predictions for spatial verification.

    -   **filepaths**. \[list\]. List with the different directories where the experiments are located. It is IMPORTANT that, even if there is only one directory, the path is preceded by a \",\". If the path contains the name of the experiment, you can replace this name by \"%exp\". The use of several paths makes it possible to use, for the same experiment, high resolution simulations that have been generated with different domains.

    -   **filename**. \[str\]. Name of the experiment file with extension, if any. It must contain the required characters to indicate the date format used by datetime. The lead time must be indicated as "%L", with as many L's as digits.

    -   **fileformat**. \[str\]. File format of the experiment file. Possible values are: netCDF, Grib.

-   inits. Initializations of the experiment to be used in the spatial verification.

    -   **\<inittime\>**. \[str\]. Format: \"%Y%m%d%H\".

        -   **path**. \[int\]. Element of the [\"format\": \"filepaths\"](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#experiment-config-file-config_expyaml) list to be used for this initialization. It is specified with an integer, where 0 indicates the first element. This allows selecting the appropriate domain in the case that two different domains of the same experiment include this initialization.

        -   **fcast_horiz**. \[str\]. Time (UTC) when the verification of this initialization is to be finished. It must be in the format \"%Y%m%d%H\". This may be because the event ends at that timestep or the experiment's forecast horizon do not reach that timestep. It also allows to exclude timesteps where the event has moved and does not fall within the domain of the experiment.

-   vars. Information regarding the variable to be used for verification.

    -   **\<var_verif\>**. \[str\]. Variable name to be verified. Possible values are: pcp (precipitation), bt (brightness temperature), rain (rainfall), refl (maximum reflectivity).

        -   **var**. \[int, str or dict\]. Variable to get from the experiment files. If [\"format\": \"extension\"](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#experiment-config-file-config_expyaml) is "Grib", \"var\" can be: 1) an integer with the message number associated to the verification variable; 2) a string in \"\<short_name\>\|\<level\>\" format; or 3) a dictionary with the keys and values of the grib message to be selected.

        -   **accum**. \[bool\]. Boolean value. It indicates whether \"var\" is cumulative or not. If true, the previous hour is subtracted from the current hour to compute the current hourly accumulated value.

        -   **postprocess**. \[str\]. If not \"None\", the code looks for this key in the postprocess_function dictionary (from [dicts.py](https://github.com/DEODE-NWP/deode_spatial_verif/blob/main/scripts/libs/dicts.py)) which will get the function with which to perform the postprocess transformation "var" to \<var_verif\>. This function must be developed in [PostProcess.py](https://github.com/DEODE-NWP/deode_spatial_verif/blob/main/scripts/libs/PostProcess.py) (note differences with [\"vars\": \<var_verif\>: \"postprocess\"](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#observation-config-file-config_obs_dbyaml)).

        -   **find_min**. \[bool\]. Boolean value. It indicates whether the variable should be analysed for minimum values. This argument allows the application of the FSS and SAL methods of [pysteps](https://github.com/pySTEPS/pysteps/blob/master/pysteps/verification/interface.py), which are developed to analyse fields above a certain threshold and not values below this threshold. For instance, brightness temperature is a magnitude where minimum values are of interest to analyse.

        -   **verif_0h**. \[bool\]. Boolean value. It indicates whether the variable can be verified at the initial time step.

    -   lat

        -   **var**. \[str\]. Latitude name to get from the experiment files. If values are 1D, a 2D meshgrid is created.

        -   **description**. \[str\]. Used as a description of this variable for regrided experiments in netCDF format.

    -   lon

        -   **var**. \[str\]. Longitude name to get from the experiment files. If values are 1D, a 2D meshgrid is created.

        -   **description**. \[str\]. Used as a description of this variable for regrided experiments in netCDF format.

# Before start...

In order to perform the spatial verification, it is necessary to have
observational databases. In addition, these databases generally need to
be processed before they can be used for verification. Some scripts have
been developed to perform this task. These scripts must be launched from
the same directory where they are located. Before running a script, the
configuration files of the observations and case study must have been
properly created. In particular:

-   config\_\<obs_db\>.yaml:

    -   format

        -   filename

    -   vars

        -   \<var_verif\>

            -   var

-   config\_\<Case\>.yaml:

    -   dates

        -   ini

        -   end

    -   location

        -   NOzoom

## scripts/downloads/download\_\<OBS\>.py

To execute these scripts, username and password in nasa (for IMERG) and
access credentials (key + password, for SEVIRI) are required. They can
be executed via terminal: `python3 download_<OBS>.py <Case> <user/key> <password/token>`

These files perform the following tasks:

*IMERG*

1.  Download 30-minutal files for the time span of the extreme event in the case study.

2.  Average two intra-hourly HDF5 files to obtain the cumulative precipitation for that hour (the original variable (precipitation) is the 1-hour precipitation rate).

3.  Extract 1D arrays of latitudes and longitudes and build a two-dimensional meshgrid with both.

4.  Save the information (variable name: pcp) in netCDF format in the OBSERVATIONS/data_IMERG_pcp/\<Case\>/ directory. The computed values correspond to the accumulated precipitation at the previous hour.

*SEVIRI*

1.  Download netCDF files with the closest scan to the hours to be verified of the event (%H:57) for a region 5º larger than the plotting domain of the case study.

2.  Compute the brightness temperature from the irradiance of channel 9 (see [PostProcess.IrradianceToBrightnessTemperature](https://github.com/DEODE-NWP/deode_spatial_verif/blob/main/scripts/libs/PostProcess.py)).

3.  Build the latitude and longitude meshgrid.

4.  Save the information (variable name: bt) in netCDF format in the OBSERVATIONS/data_SEVIRI_bt/\<Case\>/ directory. The computed values correspond to the approximate instantaneous brightness temperature of the date.

## scripts/utils/PostProccess_OPERA\_\<var_verif\>.py

OPERA raw files have been downloaded manually. They are located in the
ATOS directory: /perm/esp0754/databases/. These files are represented in
a given projection. A two-dimensional grid building procedure has been
carried out. Therefore, the PostProccess_OPERA\_\<var_verif\> scripts:

1.  Get the variable to be verified.

2.  Build the two-dimensional grid of OPERA radar.

3.  Save the values in netCDF format.

They can be executed via terminal: `python3 PostProccess_OPERA_<var_verif>.py <path_OPERA_raw> <Case>`

## using existing observations

Another possibility is to use the observations that have been previously downloaded and adapted to the tool by following [the steps discussed above](https://github.com/DEODE-NWP/deode_spatial_verif?tab=readme-ov-file#before-start). For this, the parameter [\"path\": \<path\>](https://github.com/DEODE-NWP/deode_spatial_verif?tab=readme-ov-file#observation-config-file-config_obs_dbyaml) must be set to the path where the observations have been stored and [run the verification exercise](https://github.com/DEODE-NWP/deode_spatial_verif?tab=readme-ov-file#run-spatial-verification) with the `--link_obs` option specified.

# Run spatial verification

The main.py file launches the spatial verification scripts developed in the tool. A complete verification exercise consists of 4 main and 2 optional steps. All steps are detailed below. An example of use can be found [here](https://github.com/DEODE-NWP/deode_spatial_verif?tab=readme-ov-file#example-usage).

## Main scripts

The products generated by these scripts are required to perform the
following steps. Therefore, if the program is not completed
successfully, successive programs cannot be used.

0.  The set_environment.py script creates the required folders (if they do not exist) to save the generated products. It is always executed by the main script.

1.  Storage of observations in the appropriate directory. This can be done in two ways: i) download observations using the [download](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#scriptsdownloadsdownload_obspy) or [processing](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#scriptsutilspostproccess_opera_var_verifpy) scripts; ii) the link_obs.py script creates the links to the [previously downloaded observational files](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#scriptsutilspostproccess_opera_var_verifpy) in the appropriate folder. This way is executed with the `--link_obs` argument of main.py.

2.  The regrid.py script links the simulations of an experiment to the directory (created at initial step) and performs a linear interpolation of the data to the grid of the observations to be verified. Additionally, a map with the experiment data in its original grid is generated. This plot allows to check that the variable selected in the experiment is the correct one. This step is executed with the `--run_regrid` argument of main.py.

3.  The verification.py script gets the arrays of observations and regridded experiments (generated in the previous step), crops a common verification domain and computes the FSS and SAL metrics using the [pysteps](https://github.com/pySTEPS/pysteps) module. Results are saved in several plots splitted by initializations. Additionally, plots with the FSS and SAL verification for each time step are generated. The original [SAL](https://github.com/pySTEPS/pysteps/blob/master/pysteps/verification/salscores.py) has been [modified](https://github.com/DEODE-NWP/deode_spatial_verif/blob/main/scripts/libs/customSAL.py) and a new object detection figure is now generated. In addition, object detection is further configurable (see [\"vars\": \<var_verif\>: \"SAL\": \"tstorm_kwargs\"](https://github.com/DEODE-NWP/deode_spatial_verif?tab=readme-ov-file#observation-config-file-config_obs_dbyaml) from the observations configuration file). Default values for detection objects are shown in [Appendix](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#appendix). This step is executed with the `--run_verif` argument of main.py.

4.  Finally, the tool also allows a comparison between two experiments launched for the same case study. The compExps_stats.py and compExps_maps.py scripts generate summary plots that allow comparison of the verifications conducted in the previous step for the low and high spatial resolution experiments. This comparison is performed on the timesteps verified in both experiments (initializations and lead times).

    1.  The comExps_metrics.py script generates the mean FSS comparison, the FSS distributions for each threshold and scale, the SAL scatter-plot of both experiments and the SAL distributions.

    2.  The compExps_maps.py script allows the comparison in a subjective way with a gif plot (and the frames that compose it) of the fields to be verified for each of the experiments against the observational values. In addition, an additional plot is generated with the total accumulated value during the extreme event if the variable to be verified is precipitation/rainfall or with the maximum (minimum) of the event for each point if the variable to be verified is reflectivity (brightness temperature).

## Helpful scripts

The scripts detailed below require the successful execution of some of
the main scripts.

1.  The script plot_regrid.py generates plots with maps for each timestep to be verified. Observational values are plotted in the left panel while the regridded experiments are plotted in the right panel. This script allows to check that the interpolation to the grid of observations is consistent. It is necessary to have previously executed the regrid.py script. This step is executed with the `--run_plot_regrid` argument of main.py.

2.  The script create_panels.py combines all the plots generated from the verification for a timestep. To run this program, the verification step and the plot_regrid.py script must have been run successfully previously. This script generates a 2x3 figure. The observations, the regridded experiment and the experiment with its original resolution are displayed in the top row. The bottom row shows the results of FSS, SAL and the objects found by the SAL, both the observations and the experiment. This step is executed with the `--run_panels` argument of main.py.

## Example usage

Suppose we have a case study called Spain_202205 for which two experiments have been run at different spatial resolution: AIB_46h1_de2 (2.5 km) and VAL500m_46h1_de2 (500 m). We want to compare whether there is an added value in high resolution. To this end:

-   Full spatial verification of the high resolution experiment:
python3 main.py --case Spain_202205 --exp VAL500m_46h1_de2 --link_obs --run_regrid --run_plot_regrid --run_verif --run_panels

-   Full spatial verification of the reference experiment:
python3 main.py --case Spain_202205 --exp AIB_46h1_de2 --run_regrid --run_plot_regrid --run_verif --run_panels

-   Comparison between experiments:
python3 main.py --case Spain_202205 --exp VAL500m_46h1_de2 --exp_ref AIB_46h1_de2 --run_comparison

# Integration into Deode-Workflow

We are working on the integration of the tool within the [Deode-Workflow](https://github.com/destination-earth-digital-twins/Deode-Workflow) (DW) to automate the creation of the [configuration files](https://github.com/DEODE-NWP/deode_spatial_verif/tree/main?tab=readme-ov-file#configs) needed to run a verification exercise with this tool. For this, the `--config_file` argument has been implemented. This argument allows to run a verification exercise directly from the DW configuration file, without the need to create the case study and the experiment previously, e.g.:

python3 main.py --config_file /home/snh02/PARIS_RDP/Deode-Prototype/cy46h1_harmonie_arome_paris_200m_warm.toml --link_obs --run_regrid --run_plot_regrid --run_verif --run_panels

Another possibility is to run a verification exercise directly from DW, e.g.:

deode case ?deode/data/config_files/configurations/cy46h1_harmonie_arome /home/esp0754/config_files_deode/storm_southSP_20240903.toml /home/esp0754/deode_plugins/verif_plugin.toml -o storm_southSP_20240903_verif.toml --start-suite

# Appendix

Default values for SAL methodology following the pysteps module.

|   f  |   q  | Max_num_features |      Minref     |               Maxref                |          Mindiff           |   Minmax        |
| ---- | ---- | ---------------- | --------------- | ----------------------------------- | ----------------- | --------------- |
| 1/15 | 0.95 |        None      | f·R<sub>q</sub> | f·R<sub>q</sub> + 1·10<sup>-5</sup> | 1·10<sup>-5</sup> | f·R<sub>q</sub> |

where R<sub>q</sub> is the value corresponding to q-quartile from input.

# References

Wernli, H., Paulat, M., Hagen, M., & Frei, C. (2008). SAL---A novel
quality measure for the verification of quantitative precipitation
forecasts. *Monthly Weather Review*, *136*(11), 4470-4487.

Gilleland, E., Ahijevych, D., & Ebert, B. (2009). Spatial forecast
verification methods intercomparison. *Wea. Forecasting*.
