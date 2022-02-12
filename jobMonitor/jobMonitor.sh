#!/bin/bash

# Load modules
export HPCC_MODULES=/opt/linux/centos/7.x/x86_64/pkgs
source /usr/share/init/profile.sh && module purge
source /etc/profile.d/conda.sh
module load miniconda2
conda_init

conda activate python3
SCRIPT_HOME=$(dirname $(realpath $0))

${SCRIPT_HOME}/jobMonitor.py $@