#!/bin/bash

# Check total number of cores used by a single user in each partition

source /etc/profile.d/modules.sh
module load slurm/19.05.0

echo -e "You ($USER) are using the following CPU cores per partition:"

for PART in short intel batch highmem gpu; do
    USED=$(squeue -u $USER -p $PART -o '%C' -t R -h | tr '\n' '+')0 
    echo -e "\t\e[32m$PART\t\e[33m$(echo ${USED} | bc)\e[0m"
done
