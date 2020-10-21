#!/bin/bash -l

source /etc/profile.d/modules.sh
module load R/3.6.0

Rscript /opt/linux/centos/7.x/x86_64/pkgs/iigb_utilities/1/qstatMonitor/jobMonitor.R

