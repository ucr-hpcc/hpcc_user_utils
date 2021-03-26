#!/bin/bash -l

module purge
module load iigb_utilities
module load R/3.6.0

SCRIPT=$(which $(basename $0))

if [ "$#" -gt 0 ]; then
    Rscript $(dirname $SCRIPT)/../jobMonitor/jobMonitor.R $@
else
    Rscript $(dirname $SCRIPT)/../jobMonitor/jobMonitor.R pdf
fi

