#!/bin/bash

SGROUP=$(id -gn)
IFS=$'\n'

echo -e "==============="
echo "Slurm Limits"
echo -e "==============="

for LIMIT in $(sacctmgr show account $SGROUP format=grptres%30 --ass --noheader | grep "gpu=" | sort | uniq); do
    SLURM_LIMITS="Group ALL $(echo $LIMIT | sed 's/ //g') N/A"
done
    
for LIMIT in $(sacctmgr show user $USER format=partition,grptres%30,maxsubmit --ass --noheader | sort | uniq); do
    PART=$(echo $LIMIT | awk '{print $1}' | sed 's/ //g')
    TRES=$(echo $LIMIT | awk '{print $2}' | sed 's/ //g')
    MAX=$(echo $LIMIT | awk '{print $3}' | sed 's/ //g')
    if [[ $(echo $PART | grep -P '^[a-z]') ]] && [[ -n $MAX ]]; then
       SLURM_LIMITS=$(echo -e "$SLURM_LIMITS\nUser $PART $TRES $MAX")
    elif [[ $(echo $PART | grep -P '^[a-z]') ]] && [[ -z $MAX ]]; then
       SLURM_LIMITS=$(echo -e "$SLURM_LIMITS\nUser $PART N/A $TRES") 
    fi
done

echo -e "$SLURM_LIMITS" | column -t --table-columns TYPE,PARTITION,RESOURCE,MAXSUBMIT
