#!/bin/bash

########## PREAMBLE ##########
# arguments. All arguments must have the corresponding configuration file within the subdirectories of the config folder.
OBS="SEVIRI_bt" # possible values are: "IMERG_pcp", "SEVIRI_bt", "OPERA_pcp", "OPERA_refl"
Case="Spain_202205" # case study label. It is recommended that the name matches with dcmdb if the case study is included in it.
expLowRes="AIB_46h1_de2" # label of the reference experiment. It is shown on the left in the comparisons. 
expHighRes="VAL500m_46h1_de2" # label of the high spatial resolution experiment. It is shown on the right in the comparisons. 

# subset (in coming...) 
#subset_label=""

# tasks. set true or false to indicate whether or not the tool has to perform that step of the spatial verification.
run_set_environment=true
run_regrid=true
run_plot_regrid=true
run_verif=true
run_panels=true
run_comparison=true
##############################

# run function
run_python() {
    local script=$1
    local exp=$2
    if [[ -n "$exp" && "$exp" != "" ]]; then
        python3 $script "$OBS" "$Case" "$exp"
    fi
}

# spatial verification exercise
if $run_set_environment; then
    run_python scripts/verification/set_environment.py "$expLowRes"
    run_python scripts/verification/set_environment.py "$expHighRes"
fi

if $run_regrid; then
    run_python scripts/verification/regrid.py "$expLowRes"
    run_python scripts/verification/regrid.py "$expHighRes"
fi

if $run_plot_regrid; then
    run_python scripts/utils/plot_regrid.py "$expLowRes"
    run_python scripts/utils/plot_regrid.py "$expHighRes"
fi

if $run_verif; then
    run_python scripts/verification/verification.py "$expLowRes"
    run_python scripts/verification/verification.py "$expHighRes"
fi

if $run_panels; then
    run_python scripts/utils/create_panels.py "$expLowRes"
    run_python scripts/utils/create_panels.py "$expHighRes"
fi

if $run_comparison && [[ "$expLowRes" != "" && "$expHighRes" != "" ]]; then
    python3 scripts/verification/compExps_metrics.py ${OBS} ${Case} "${expLowRes}-VS-${expHighRes}"
    python3 scripts/verification/compExps_maps.py ${OBS} ${Case} "${expLowRes}-VS-${expHighRes}"
fi
