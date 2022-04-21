#!/bin/bash

# Load modules
export HPCC_MODULES=/opt/linux/rocky/8.x/x86_64/pkgs
source /usr/share/Modules/init/profile.sh && module purge
source /etc/profile.d/conda.sh
module -s load slurm anaconda

SCRIPT_HOME=$(dirname $(realpath $0))

${SCRIPT_HOME}/jobMonitor.py $@
