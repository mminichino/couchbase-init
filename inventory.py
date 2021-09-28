#!/usr/bin/env python

'''
Dynamic inventory script for db-host-prep
'''

import os
import sys
import argparse
import json
import boto3
import socket
import dns.resolver
import dns.reversename

class dynamicInventory(object):

    def __init__(self):
        self.inventory = {}

        self.parse_args()

        if "LAB_ID" not in os.environ:
             self.inventory = self.empty_inventory()
        elif self.args.list:
            self.labId = os.environ['LAB_ID']
            self.inventory = self.lab_inventory()
        elif self.args.host:
            self.inventory = self.empty_hostvars()
        else:
            self.inventory = self.empty_hostvars()

        print(json.dumps(self.inventory))

    def lab_inventory(self):
        inventoryJson = {}
        inventoryJson['lab'] = {"hosts": [], "vars": {}}
        inventoryJson['_meta'] = {"hostvars": {}}
        hostname = socket.gethostname()
        homeDir = os.environ['HOME']
        dnsKeyFile = homeDir + "/.dns/dns.key"

        filters = [
            {
                'Name': 'tag:LabName',
                'Values': [self.labId]
            }
        ]

        try:
            ip_result = dns.resolver.query(hostname, 'A')
            arpa_result = dns.reversename.from_address(ip_result[0].to_text())
            fqdn_result = dns.resolver.query(arpa_result, 'PTR')
            host_fqdn = fqdn_result[0].to_text()
            domain_name = host_fqdn.split('.',1)[1].rstrip('.')

            inventoryJson['lab']['vars']['domain'] = domain_name
        except dns.resolver.NXDOMAIN:
            pass

        try:
            if os.environ['AWS_DEFAULT_REGION']:
                inventoryJson['lab']['vars']['region'] = os.environ['AWS_DEFAULT_REGION']
        except KeyError:
            print("Please set the AWS_DEFAULT_REGION environment variable.")
            sys.exit(1)

        try:
            ec2 = boto3.resource('ec2')
            instances = ec2.instances.filter(Filters=filters)

            instanceTags = []
            for instance in instances:
                instanceId = instance.id
                instanceJson = {'Id': instanceId}
                for tags in instance.tags:
                    instanceJson[tags["Key"]] = tags["Value"]
                instanceTags.append(instanceJson)
        except (botocore.exceptions.NoRegionError, botocore.exceptions.ClientError) as e:
            print("Please configure the environment for AWS access: %s" % str(e))
            sys.exit(1)

        instanceTags.sort(key=lambda x: x["Name"])

        for x in range(len(instanceTags)):
            if instanceTags[x]['Name']:
                if instanceTags[x]['Role']:
                    if instanceTags[x]['Role'] == "database":
                        inventoryJson['lab']['hosts'].append(instanceTags[x]['Name'])

        return inventoryJson

    def empty_hostvars(self):
        return {'_meta': {'hostvars': {}}}

    def empty_inventory(self):
        inventoryJson = {}
        inventoryJson['lab'] = {"hosts": [], "vars": {}}
        inventoryJson['_meta'] = {"hostvars": {}}
        return inventoryJson

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

def main():
    dynamicInventory()

if __name__ == '__main__':

    try:
        main()
    except SystemExit as e:
        if e.code == 0:
            os._exit(0)
        else:
            os._exit(e.code)
