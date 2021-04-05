#!/bin/bash

SGROUP=$(id -gn)
IFS=$'\n'

echo -e "==============="
echo "Slurm Limits"
echo -e "==============="

#for LIMIT in $(sacctmgr show account $SGROUP format=partition,grptres%30 --ass --noheader | sed "s/$SGROUP.*//g" | sed "s/\sgpu.*//g" | sort | uniq); do
#for LIMIT in $(sacctmgr show account $SGROUP format=partition,grptres%30 --ass --noheader | sed "s/\sgpu.*//g" | sort | uniq); do
for LIMIT in $(sacctmgr show account $SGROUP format=partition,grptres%30,user%30 --ass --noheader | grep -P "$USER\s*$|gpu\=" | sed "s/\s*$USER\s*//g" | grep -v '^\s*gpu\s*$' | sort | uniq); do
    TRIM_LIMIT=$(echo $LIMIT | sed 's/ //g')
    echo $TRIM_LIMIT | grep 'gres' &> /dev/null
    EXIT=$?
    if [[ $EXIT -eq 0 ]]; then
        echo -e "\tGroup Limits"
        echo -e "\t---------------"
        echo -e "\t     ALL\t\t$TRIM_LIMIT"
        echo -e "\n\tUser Limits"
        echo -e "\t---------------"
    else
        echo -e "\t$LIMIT"
    fi
done

#sacctmgr show account operations --ass format=Partition,GrpTRES%30 --noheader | sed "s/$SGROUP.*//g" | sed "s/\sgpu.*//g" | sort | uniq
