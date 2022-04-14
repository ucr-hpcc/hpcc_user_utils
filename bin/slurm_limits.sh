#!/bin/bash

SGROUP=$(id -gn)
IFS=$'\n'

echo -e "==============="
echo "Slurm Limits"
echo -e "==============="

echo -e "\tGroup Limits"
echo -e "\t---------------"
for LIMIT in $(sacctmgr show account $SGROUP format=grptres%30 --ass --noheader | grep "gpu=" | sort | uniq); do
    TRIM_LIMIT=$(echo $LIMIT | sed 's/ //g')
    echo -e "\n\tALL\t\t$TRIM_LIMIT"
done
    
echo -e "\n\tUser Limits"
echo -e "\t---------------"
for LIMIT in $(sacctmgr show user $USER format=partition,grptres%30 --ass --noheader | sort | uniq); do
    PART=$(echo $LIMIT | awk '{print $1}' | sed 's/ //g')
    TRES=$(echo $LIMIT | awk '{print $2}' | sed 's/ //g')
    echo -e "\t$PART\t\t$TRES"
done

