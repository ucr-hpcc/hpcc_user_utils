#!/opt/linux/centos/7.x/x86_64/pkgs/cfncluster/1.4/cfncluster/bin/python

# -*- coding: utf-8 -*-
####### Load modules ##########
from cfncluster.cli import main
import re
import subprocess
from subprocess import Popen, PIPE
import time
import os
import sys
import argparse
import ConfigParser
import boto
from boto import iam
from StringIO import StringIO
import signal

########## Get location of users cfncluster config file   ###########
homepath = os.environ['HOME']
clusterconfigfile = homepath + "/.cfncluster/config"

########## Get location of users aws credentials file   ###########
homepath = os.environ['HOME']
dotaws = homepath + "/.aws"
awscredentialsfile = homepath + "/.aws/credentials"

try:
    os.makedirs(dotaws)
except:
    dircreated = 1

########## Template Section
"""
Pulled templates from here:
    http://cfncluster.readthedocs.io/en/latest/iam.html
"""

CfnClusterInstancePolicy = \
"""{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Resource": [
                "*"
            ],
            "Action": [
                "ec2:AttachVolume",
                "ec2:DescribeInstanceAttribute",
                "ec2:DescribeInstanceStatus",
                "ec2:DescribeInstances"
            ],
            "Sid": "EC2",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "*"
            ],
            "Action": [
                "dynamodb:ListTables"
            ],
            "Sid": "DynamoDBList",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "arn:aws:sqs:%(REGION)s:%(AWS_ACCOUNT_ID)s:cfncluster-*"
            ],
            "Action": [
                "sqs:SendMessage",
                "sqs:ReceiveMessage",
                "sqs:ChangeMessageVisibility",
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl"
            ],
            "Sid": "SQSQueue",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "*"
            ],
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "autoscaling:SetDesiredCapacity"
            ],
            "Sid": "Autoscaling",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "*"
            ],
            "Action": [
                "cloudwatch:PutMetricData"
            ],
            "Sid": "CloudWatch",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "arn:aws:dynamodb:%(REGION)s:%(AWS_ACCOUNT_ID)s:table/cfncluster-*"
            ],
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:GetItem",
                "dynamodb:DeleteItem",
                "dynamodb:DescribeTable"
            ],
            "Sid": "DynamoDBTable",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "*"
            ],
            "Action": [
                "sqs:ListQueues"
            ],
            "Sid": "SQSList",
            "Effect": "Allow"
        },
        {
            "Resource": [
                "arn:aws:logs:*:*:*"
            ],
            "Action": [
                "logs:*"
            ],
            "Sid": "CloudWatchLogs",
            "Effect": "Allow"
        }
    ]
}
"""

CfnClusterUserPolicy = \
"""{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "EC2Describe",
            "Action": [
                "ec2:DescribeKeyPairs",
                "ec2:DescribeVpcs",
                "ec2:DescribeSubnets",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribePlacementGroups",
                "ec2:DescribeImages",
                "ec2:DescribeInstances",
                "ec2:DescribeSnapshots",
                "ec2:DescribeVolumes",
                "ec2:DescribeVpcAttribute",
                "ec2:DescribeAddresses",
                "ec2:CreateTags",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeAvailabilityZones"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "EC2Modify",
            "Action": [
                "ec2:CreateVolume",
                "ec2:RunInstances",
                "ec2:AllocateAddress",
                "ec2:AssociateAddress",
                "ec2:AttachNetworkInterface",
                "ec2:AuthorizeSecurityGroupEgress",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:CreateNetworkInterface",
                "ec2:CreateSecurityGroup",
                "ec2:ModifyVolumeAttribute",
                "ec2:ModifyNetworkInterfaceAttribute",
                "ec2:DeleteNetworkInterface",
                "ec2:DeleteVolume",
                "ec2:TerminateInstances",
                "ec2:DeleteSecurityGroup",
                "ec2:DisassociateAddress",
                "ec2:RevokeSecurityGroupIngress",
                "ec2:ReleaseAddress"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "AutoScalingDescribe",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeAutoScalingInstances"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "AutoScalingModify",
            "Action": [
                "autoscaling:CreateAutoScalingGroup",
                "autoscaling:CreateLaunchConfiguration",
                "autoscaling:PutNotificationConfiguration",
                "autoscaling:UpdateAutoScalingGroup",
                "autoscaling:PutScalingPolicy",
                "autoscaling:DeleteLaunchConfiguration",
                "autoscaling:DescribeScalingActivities",
                "autoscaling:DeleteAutoScalingGroup",
                "autoscaling:DeletePolicy"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "DynamoDBDescribe",
            "Action": [
                "dynamodb:DescribeTable"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "DynamoDBModify",
            "Action": [
            "dynamodb:CreateTable",
            "dynamodb:DeleteTable"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchModify",
            "Action": [
                "cloudwatch:PutMetricAlarm",
                "cloudwatch:DeleteAlarms"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "SQSDescribe",
            "Action": [
                "sqs:GetQueueAttributes"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "SQSModify",
            "Action": [
                "sqs:CreateQueue",
                "sqs:SetQueueAttributes",
                "sqs:DeleteQueue"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "SNSDescribe",
            "Action": [
            "sns:ListTopics",
            "sns:GetTopicAttributes"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "SNSModify",
            "Action": [
                "sns:CreateTopic",
                "sns:Subscribe",
                "sns:DeleteTopic"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "CloudFormationDescribe",
            "Action": [
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStackResources",
                "cloudformation:DescribeStacks",
                "cloudformation:ListStacks"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "CloudFormationModify",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:DeleteStack",
                "cloudformation:UpdateStack"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Sid": "S3CfnClusterReadOnly",
            "Action": [
                "s3:Get*",
                "s3:List*"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:s3:::%(REGION)s-cfncluster*"
            ]
        },
        {
            "Sid": "IAMModify",
            "Action": [
                "iam:PassRole"
            ],
            "Effect": "Allow",
            "Resource": "arn:aws:iam::%(AWS_ACCOUNT_ID)s:role/%(CFNCLUSTER_EC2_ROLE_NAME)s"
        }
    ]
}
"""

HpccS3Policy = \
"""{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:Get*",
                "s3:List*"
            ],
            "Resource": [
                "arn:aws:s3:::hpcc-software",
                "arn:aws:s3:::hpcc-software/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::420368308087:role/cfncluster-s3-external"
        }
    ]
}
"""

def ConfigSectionMap(section):
    Config = ConfigParser.ConfigParser()
    Config.read(clusterconfigfile)
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def SetComputeInstanceType(computeinstancetype):
    ###### Initailize ConfigParser and read in config file
    Config = ConfigParser.ConfigParser()
    Config.read(clusterconfigfile)
    ###### Set Values for config file 
    Config.set('cluster default', 'compute_instance_type', computeinstancetype)
    ###### Write to config file 
    with open(clusterconfigfile, 'w') as configfile:
        Config.write(configfile)
    print("Node type set to: %s" % computeinstancetype)
    exit()

def ReportComputeInstanceType():
    ###### Initailize ConfigParser and read in config file
    Config = ConfigParser.ConfigParser()
    Config.read(clusterconfigfile)
    ###### Set Values for config file update
    compute_instance_type = ConfigSectionMap("cluster default")['compute_instance_type']
    print("Current node type = %s" % compute_instance_type)
    exit()
    
  
def configurenodetype():
    if sys.argv[1] == "nodetype":
        if len(sys.argv) >= 3:
            if sys.argv[2] == "test":
                SetComputeInstanceType('t2.micro')
            if sys.argv[2] == "base":
                SetComputeInstanceType('c5.2xlarge')
            if sys.argv[2] == "gpu":
                SetComputeInstanceType('p2.8xlarge')
            if sys.argv[2] == "highmem":
                SetComputeInstanceType('r4.large')
        ReportComputeInstanceType()
 
def createcfnconfig():
    if sys.argv[1] == "configure":
        ###### Initailize ConfigParser and read in config file
        Config = ConfigParser.ConfigParser()
        Config.read(clusterconfigfile)

        ###### Set Values for config file update
        Config.set('cluster default', 'base_os', 'centos7')
        Config.set('cluster default', 'compute_instance_type', 'c5.2xlarge')
        Config.set('cluster default', 'master_instance_type', 'c5.large')
        Config.set('cluster default', 'master_root_volume_size', '70')
        Config.set('cluster default', 'scheduler', 'slurm')
        Config.set('cluster default', 'initial_queue_size', '1')
        Config.set('cluster default', 'max_queue_size', '3')
        Config.set('cluster default', 'maintain_initial_size', 'true')
        Config.set('cluster default', 'custom_ami', 'ami-d19780b1')
        Config.set('cluster default', 'shared_dir', '/scratch')
        Config.set('cluster default', 'ebs_settings', 'scratch')
        Config.set('cluster default', 'ec2_iam_role', 'hpcc-ec2-role')
        Config.add_section('ebs scratch')
        Config.set('ebs scratch', 'volume_size', '100')
        Config.set('ebs scratch', 'volume_type', 'gp2')

        aws_access_key_id = ConfigSectionMap("aws")['aws_access_key_id']
        aws_secret_access_key = ConfigSectionMap("aws")['aws_secret_access_key']

        ###### Write to config file adding and overwrite values
        with open(clusterconfigfile, 'w') as configfile:
            Config.write(configfile)
	return aws_access_key_id,aws_secret_access_key

def createawscredentials(aws_access_key_id,aws_secret_access_key):
    
    ###### Initialize another instance of configparser
    Credentials = ConfigParser.ConfigParser()
    Credentials.readfp(StringIO('[default]'))
    Credentials.set('default', 'aws_access_key_id', aws_access_key_id)
    Credentials.set('default', 'aws_secret_access_key', aws_secret_access_key)

    ###### Create AWS credentials file
    with open(awscredentialsfile, 'w') as awscredentials:
        Credentials.write(awscredentials)

def setawspol():
    # Connect to AWS iam service
    iam_conn = boto.iam.connection.IAMConnection()

    # Pull iam account user names
    user_info = dict()
    for user in iam_conn.get_all_users()['list_users_response']['list_users_result']['users']:
        user_info[user["user_name"]] = user['arn'].split(':')[4]

    
    # Show IAM user names and capture choice 
    print('Acceptable Values for IAM user name:')
    for key in user_info.keys():
        print('    {0}'.format(str(key)))

    user_name = raw_input("Enter IAM user name []: ")
    REGION = 'us-west-1'
    HPCC_EC2_ROLE_NAME = "hpcc-ec2-role"

    # Input checking ensure user name provided is valid
    if user_name not in user_info.keys():
        raise Exception('Invalid AWS user name')
    else:
        AWS_ACCOUNT_ID = user_info[user_name]

    # Populate templates and create final policy documents
    ec2_policy = CfnClusterInstancePolicy % {'REGION':REGION,'AWS_ACCOUNT_ID':AWS_ACCOUNT_ID}
    iam_policy = CfnClusterUserPolicy % {'REGION':REGION,'AWS_ACCOUNT_ID':AWS_ACCOUNT_ID,'CFNCLUSTER_EC2_ROLE_NAME':HPCC_EC2_ROLE_NAME}
    s3_policy = HpccS3Policy

    # Create e2c, iam, s3 policies
    try:
        ec2_arn = iam_conn.create_policy("hpcc-ec2-policy", policy_document=ec2_policy, path='/', description="HPCC ec2 policy")\
        ['create_policy_response']['create_policy_result']['policy']['arn']
        iam_arn = iam_conn.create_policy("hpcc-iam-policy", policy_document=iam_policy, path='/', description="HPCC iam policy")\
        ['create_policy_response']['create_policy_result']['policy']['arn']
        s3_arn = iam_conn.create_policy("hpcc-s3-policy", policy_document=s3_policy, path='/', description="HPCC s3 policy")\
        ['create_policy_response']['create_policy_result']['policy']['arn']
        # Create role for ec2 instances
        iam_conn.create_role(HPCC_EC2_ROLE_NAME, assume_role_policy_document=None, path=None)
        # Attach ec2 and s3 policies to ec2 role
        iam_conn.attach_role_policy(ec2_arn, HPCC_EC2_ROLE_NAME)
        iam_conn.attach_role_policy(s3_arn, HPCC_EC2_ROLE_NAME)
        # Create instance profile
        iam_conn.create_instance_profile(HPCC_EC2_ROLE_NAME, path='/')

        # Attach role to instance profile
        iam_conn.add_role_to_instance_profile(HPCC_EC2_ROLE_NAME, HPCC_EC2_ROLE_NAME)
    except:
        theerror='failed to Attach role to instance profile'

def configureuser():
        if sys.argv[1] == "configure":
	    aws_access_key_id,aws_secret_access_key = createcfnconfig()
            createawscredentials(aws_access_key_id,aws_secret_access_key)
	    setawspol()
    
def signal_handler(signal, frame):
    print('')
    sys.exit(0)

 

########## Main Code ##########
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    if len(sys.argv) <= 1:
	main()
    if len(sys.argv) >= 1:
        configurenodetype()
    main()
    configureuser()
    exit()
