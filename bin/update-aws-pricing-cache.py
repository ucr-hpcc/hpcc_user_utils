#!/opt/linux/centos/7.x/x86_64/pkgs/cfncluster/1.4/cfncluster/bin/python

# -*- coding: utf-8 -*-
####### Load modules ##########
import os, sys, json, time, requests

AWSPricingCacheFile = 'aws-price-cache-file'

def UpdateAwsPricingCache(AWSPricingCacheFile):
    response = requests.get('https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-west-1/index.json')
    offer = json.loads(response.text)
    with open(AWSPricingCacheFile, 'w') as f:
        f.write(json.dumps(offer))


UpdateAwsPricingCache(AWSPricingCacheFile)
