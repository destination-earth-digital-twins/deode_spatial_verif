#!/bin/bash

########## PREAMBLE ##########
# arguments
OBS="SEVIRI_bt"
Case="VALENCIA"
expLowRes="AIB_46h1_de2"
expHighRes="VAL500m_46h1_de2"

# tasks
run_set_environment=true
run_regrid=true
run_plot=true
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

if $run_plot; then
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
    python3 scripts/scripts/verification/compExps_metrics.py ${OBS} ${Case} "${expLowRes}-VS-${expHighRes}"
    python3 scripts/scripts/verification/compExps_maps.py ${OBS} ${Case} "${expLowRes}-VS-${expHighRes}"
fi
