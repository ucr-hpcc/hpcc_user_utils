#!/usr/bin/env python3

import json
import sys
# To run bash command
import subprocess
import re
import numpy as np
import io
#for checking if username exist
import pwd
import os
from collections import OrderedDict
#for parsing argument
import sys
if len(sys.argv) == 1 or sys.argv[1] != "-h" or sys.argv[1] != "--help":
  # bash command so it does not need to be run multiple time
  #scontrol -a show node -o
  scontrol, scontrol_error = subprocess.Popen(['/opt/linux/centos/7.x/x86_64/pkgs/slurm/19.05.0/bin/scontrol', '-a', 'show', 'node', '-o'], stdout=subprocess.PIPE, universal_newlines=True).communicate()

  #used to get username that is running on the 
  #sacct -n --delimiter "|" --parsable2 --allusers --format User,NodeList,Partition,AllocGRES,AllocTRES,State
  sacct, sacct_error = subprocess.Popen(['/opt/linux/centos/7.x/x86_64/pkgs/slurm/19.05.0/bin/sacct', '-n', '--delimiter', '"|"', '--parsable2', '--allusers', '--format', 'User,NodeList,Partition,AllocGRES,AllocTRES,State'], stdout=subprocess.PIPE, universal_newlines=True).communicate()
  sacct = sacct.replace('"', '')
  list_of_jobs = np.genfromtxt(io.StringIO(sacct), delimiter="|", dtype="U")
  #return all running jobs
  running_jobs = list_of_jobs[np.where(list_of_jobs[:,5]=='RUNNING')]

def node( user_group_partition = None ):
  partitions = get_partition ( user_group_partition )
  print ("############################################################################################################")
  print ("Node Resources Usage Per Partition")
  print ("############################################################################################################")
  # the partitions string contains whitespaces in front of each partition name, so we need to remove it
  for partition in partitions.replace(" ","").splitlines():
    #header
    counter = 1
  
    #to parse out IDLE and DOWN machine
    idle_node = []
    down_node = []
  
    #header
    print ("============================================================================================================")
    print ( partition.upper(), "partition")
    print ("============================================================================================================")
    print ( "{0:4} {1:10} {2:10} {3:10} {4:20} {5:30}".format("", "Node", "CPU", "GPU", "MEM", "USER") )
    for line in scontrol.splitlines():
      if partition in line:
        # Node Total_cpu Used_cpu Total_gpu Used_gpu Total_mem Used_mem
        # Split the line so it is easier to parse by using array
        split_line  = line.split(" ")
        node = split_line[0].split("=")[1]
        
        #get a list of users on the nodes
        list_of_array_of_node = np.where( running_jobs[:,1]==node)
        #drop off first element, since it is an empty element, and comma delimter list
        unique_list_of_user = ",".join(str(user) for user in np.unique( running_jobs[list_of_array_of_node][:,0])[1:] )
  
        # to account for server that are offline, so it is not able to detect the Arch column
        if ( "Arch" not in split_line[1] or "State=DOWN" in line ):
          print ( "{0:4} {1:10} {2:10} {3:10} {4:20}".format(counter,
            node,
            "DOWN", 
            "DOWN",
            "DOWN"
          ))
        elif ( "Arch" in split_line[1] ):
          #loop over the current line to find AllocTRES and CfgTRES
          #sometime different node has AllocTRES and CfgTRES in different array
          for i in enumerate(split_line):
            if "AllocTRES" in i[1]:
              used = tres_parse(i[1])
            if "CfgTRES" in i[1]:
              total = tres_parse(i[1])
          
          print ( "{0:4} {1:10} {2:10} {3:10} {4:20} {5:30}".format(counter,
            node,
            str(used[0]) + "/" + str(total[0]), 
            str(used[1]) + "/" + str(total[1]),
            str(used[2]) + "/" + str(total[2]) + "G",
            unique_list_of_user
          ))
  
          counter += 1
        if "charmander"in line or "parrot" in line or "pelican" in line or "penguin" in line or "pigeon" in line:
          continue
        if "State=IDLE" in line:
          idle_node.append(line.split(" ")[0].split("=")[1])
        if "State=DOWN" in line:
          down_node.append(line.split(" ")[0].split("=")[1])
    # print (idle_node, down_node)
    print ("There are", len(idle_node) , "Entirely Idle Nodes:", " ".join(str(node) for node in idle_node ))
    print ("There are", len(down_node), "Nodes Down:", " ".join(str(node) for node in down_node ))
    print ()
  print ("############################################################################################################")
def user( user_group_partition = None ):
  partitions = get_partition ( user_group_partition )
  print ("User Resources Usage Per Partition")
  print ("############################################################################################################")
  # the partitions string contains whitespaces in front of each partition name, so we need to remove it
  for partition in partitions.replace(" ","").splitlines():
    #get a list of unique user, skipping the first elements, since it is just a blank
    unique_user = np.unique(running_jobs[:,0])[1:]
    
    #header
    print ("============================================================================================================")
    print ( partition.upper(), "partition")
    print ("============================================================================================================")
    print ( "{0:4} {1:15}  {2:4} {3:3} {4:6}".format("", "User", "CPU", "GPU", "GB_MEM") )
    counter = 1
    for user in unique_user:
      #reset variable to 0
      cpu = 0
      gpu = 0
      total_mem = 0
      # print ( user )
      user_job = running_jobs[np.where(running_jobs[:,0]==user)]
      for metric in user_job:
        if partition in metric:
          # parsed_metric = [cpu, gpu, memory]
          parsed_metric = tres_parse ( metric[4] )
          total_mem += parsed_metric[2]
          if partition in metric[2]:
            cpu += parsed_metric[0]
            gpu += parsed_metric[1]
      #this is so it skip display the username, cpu, gpu and total memory if they are all 0
      if cpu == gpu == total_mem == 0:
        continue
      print ( "{0:4} {1:15} {2:4} {3:3}  {4:6}".format(counter, user, cpu, gpu, total_mem) )
      
      counter += 1
    print ()
  print ("############################################################################################################")
def job_history ( user_group_partition = None ):
  unique_user = np.unique(list_of_jobs[:,0])[1:]
  
  partitions = get_partition ( user_group_partition )
  print ("User Job Status Per Partition")
  print ("############################################################################################################")
  for partition in partitions.replace(" ","").splitlines():
    partition_jobs = list_of_jobs[np.where(list_of_jobs[:,2]==partition)]
    #header
    print ("============================================================================================================")
    print ( partition.upper(), "partition")
    print ("============================================================================================================")
    print ( "{0:3} {1:19} {2:7} {3:9} {4:9} {5:9} {6:6} {7:7} {8:9} {9:13} {10:7}".format("", "USER", "PENDING", "SUSPENDED", "COMPLETED", "CANCELLED", "FAILED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY", "RUNNING") )
    counter = 1
    for user in unique_user:
      user_list_of_jobs = partition_jobs[np.where(partition_jobs[:,0]==user)]
      cancelled = np.where(user_list_of_jobs[:,5]=="CANCELLED")[0].size
      completed = np.where(user_list_of_jobs[:,5]=="COMPLETED")[0].size
      failed = np.where(user_list_of_jobs[:,5]=="FAILED")[0].size
      node_fail = np.where(user_list_of_jobs[:,5]=="NODE_FAIL")[0].size
      out_of_memory = np.where(user_list_of_jobs[:,5]=="OUT_OF_MEMORY")[0].size
      pending = np.where(user_list_of_jobs[:,5]=="PENDING")[0].size
      running = np.where(user_list_of_jobs[:,5]=="RUNNING")[0].size
      suspended = np.where(user_list_of_jobs[:,5]=="SUSPENDED")[0].size
      timeout = np.where(user_list_of_jobs[:,5]=="TIMEOUT")[0].size
      if pending == suspended == completed == cancelled == failed == timeout == node_fail == out_of_memory == running == 0:
        continue
      print ( "{0:3} {1:19} {2:7} {3:9} {4:9} {5:9} {6:6} {7:7} {8:9} {9:13} {10:7}".format(counter, user, pending, suspended, completed, cancelled, failed, timeout, node_fail, out_of_memory, running) )
      counter += 1
    print ()
  print ("############################################################################################################")
def tres_parse( tres ):
    ## This is for Used metric
    # Sample tres
    # CfgTRES=cpu=64,mem=500000M,billing=186
    # AllocTRES=cpu=59,mem=326G
    # CfgTRES=cpu=32,mem=115000M,billing=68,gres/gpu=4
    # AllocTRES=cpu=12,mem=96G,gres/gpu=3

    # setup, and assume all metric are 0
    cpu = 0
    gpu = 0
    mem = 0
    
    #strip out the TRES part from string
    tres = tres.replace("CfgTRES=","")
    tres = tres.replace("AllocTRES=","")
    # if tres is empty, we assume that it is offline or no one is running anything on it
    if not tres:
      return ( 0, 0, 0 )
    for metric in tres.split(","):
      if "cpu" in metric:
        cpu = int(metric.split("=")[1])
      if "gpu" in metric:
        gpu = int(metric.split("=")[1])
      if "mem" in metric:
        #capture the number after mem=
        mem = float(re.match("mem=(\d.*)[MGT]", metric ).groups()[0])

        #convert Megabyte and Terabyte to Gigabyte        
        if "M" in metric:
          mem = round( mem / 1024, 1 )
        if "T" in metric:
          mem = round( mem * 1024, 1 )
    return ( cpu, gpu, mem)

def is_user ( user ):
  try:
      pwd.getpwnam(user)
      return True
  except KeyError:
      return False

def is_partition ( partition ):
  #sinfo -p partition --noheader
  partitions, partitions_error = subprocess.Popen(['/opt/linux/centos/7.x/x86_64/pkgs/slurm/19.05.0/bin/sinfo', '-p', partition, '--noheader'], stdout=subprocess.PIPE, universal_newlines=True).communicate()
  #if sinfo returns nothing, then this is not a partition
  if not partitions:
    return False
  return True

def get_partition ( user_group_partition = None):
  # if no variable is passed into user_group_partion, we assume it is for the current user
  if not user_group_partition:
    #sacctmgr show user username format=partition --ass --noheader
    #get a list of partition the current user has
    partitions, partitions_error = subprocess.Popen(['/opt/linux/centos/7.x/x86_64/pkgs/slurm/19.05.0/bin/sacctmgr', 'show', 'user', os.getlogin(), 'format=partition', '--ass', '--noheader'], stdout=subprocess.PIPE, universal_newlines=True).communicate()
  elif is_user( user_group_partition ):
    partitions, partitions_error = subprocess.Popen(['/opt/linux/centos/7.x/x86_64/pkgs/slurm/19.05.0/bin/sacctmgr', 'show', 'user', user_group_partition, 'format=partition', '--ass', '--noheader'], stdout=subprocess.PIPE, universal_newlines=True).communicate()
  # we assume that partition and groups are the same thing
  # no point to use the group if they do not have any partition(s)
  elif is_partition( user_group_partition ):
    partitions = user_group_partition
  else:
    print (user_group_partition, "is not a valid user, group, or partition")
    quit ( 1 )
  #make the partition list to be unique, in case there are duplicate
  return "\n".join(list(OrderedDict.fromkeys(partitions.split("\n"))))

if __name__ == "__main__":
  if len(sys.argv) == 1:
    node ()
    user ()
    job_history()
  elif len(sys.argv) == 2:
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
      print ("usage:", sys.argv[0], """partition
      -h, --help            show this help message and exit
      partition             this can be user name, group, or partition name
                            if none is given, it will process all partition current user is in
      """
      )
      exit()
    node ( sys.argv[1])
    user ( sys.argv[1])
    job_history ( sys.argv[1])
    
    