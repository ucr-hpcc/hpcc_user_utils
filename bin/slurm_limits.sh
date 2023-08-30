#!/bin/bash

SGROUP=$(id -gn)
IFS=$'\n'

echo -e "==============="
echo "Slurm Limits"
echo -e "==============="

echo """
Please refer to out website for more detail quotas:
https://hpcc.ucr.edu/manuals/hpc_cluster/queue/
"""

for LIMIT in $(sacctmgr show account $SGROUP parent=ucr --assoc format=grptres%30 --noheader -p | sort | uniq); do
  GROUP_LIMITS="Group|ALL|$(echo $LIMIT | awk -F'|' '{print $1}')||"
done
    
for LIMIT in $(sacctmgr show user $USER format=partition,grptres%30,maxtresperjob%30,maxsubmit --assoc --noheader -p | sort | uniq); do
  PART=$(echo $LIMIT | awk -F'|' '{print $1}')
  TOT=$(echo $LIMIT | awk -F'|' '{print $2}')
  PERJOB=$(echo $LIMIT | awk -F'|' '{print $3}')
  MAX=$(echo $LIMIT | awk -F'|' '{print $4}')

  USER_LIMITS=$(echo -e "${USER_LIMITS}\nUser|$PART|$TOT|$PERJOB|$MAX")
done

SLURM_LIMITS="${GROUP_LIMITS}\n${USER_LIMITS}"

echo -e "$SLURM_LIMITS" | column -o '   ' -t --separator='|' --table-columns 'TYPE,PARTITION,TOTAL,PER JOB,MAXSUBMIT'
