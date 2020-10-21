#!/bin/bash

# Check total number of cores used by your group in the all partitions

source /etc/profile.d/modules.sh
module load slurm/19.05.0

if [[ -z $1 ]]; then
    GROUP=$(id -gn)
else
    GROUP=$1
fi

TOTAL=$(slurm_limits.sh | grep ALL | grep -oP 'cpu=[0-9]+' | sed 's/cpu=//g')

USED=$(squeue -A $GROUP -o '%C' -t R -h | tr '\n' '+' | sed 's/+$//g')
if [[ -z $USED ]]; then
    echo "Your group ($GROUP) is not currently using any cores."
else
    echo "Your group ($GROUP) is currently using the following number of cores: $(echo $USED | bc)/$TOTAL"
fi

