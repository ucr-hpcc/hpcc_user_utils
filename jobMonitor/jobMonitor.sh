#!/bin/bash -l

source /etc/profile.d/hpcc_modules.sh
module load R/3.6.0

SCRIPT=$(which $(basename $0))

if [ "$#" -gt 0 ]; then
    Rscript $(dirname $SCRIPT)/../jobMonitor/jobMonitor.R $@
else
    Rscript $(dirname $SCRIPT)/../jobMonitor/jobMonitor.R pdf
fi

