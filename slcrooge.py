#!/usr/bin/env python3
#                                        -*- coding:utf-8 -*-
#
#  slmon.py: get information utility
#  Created by NAKAJIMA Takaaki 
#  Last modified: Apr 16, 2014.
#
#  Require: Python v3
#
#  See also https://softlayer-api-python-client.readthedocs.org
#
# You should set env variables
# SL_USERNAME = YOUR_USERNAME
# SL_API_KEY = YOUR_API_KEY

import logging
import json
import csv
import datetime

import SoftLayer
client = SoftLayer.Client()

logger = logging.getLogger()

# ----------------------------------------------------------------------

class IterableItems:
    u"""Iterator for Pagenated list"""
    
    def __init__(self, client, limit=10):
        self.master_account = client['Account']
        self.offset = 0
        self.limit = limit
        self.define_fetch_method()
        self.fetched = self.fetch()
        
    def define_fetch_method(self):
        u"""MUST be implemented in inherited class"""
        # self.fetch_method に適切な pagenate メソッドを設定
        raise NotImpementedError("Not implemented yet.")        
    
    def fetch(self):
        items = self.fetch_method(limit=self.limit, offset=self.offset)
        self.offset += self.limit
        return items
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if len(self.fetched) < 1:
            raise StopIteration
        item = self.fetched.pop()
        if len(self.fetched) < 1:  # prefetch for next
            self.fetched = self.fetch()
        return item
    

class Users(IterableItems):
    u"""List of SoftLayer_User_Customer"""
    def define_fetch_method(self):
        self.fetch_method = self.master_account.getUsers

class VirtualGuests(IterableItems):
    u"""List of SoftLayer_Virtual_Guest"""
    def define_fetch_method(self):
        self.fetch_method = self.master_account.getVirtualGuests

class BillingItems(IterableItems):
    u"""List of SoftLayer_Billing_Item"""
    def define_fetch_method(self):
        self.fetch_method = master_account.getAllBillingItems

# --------------------------------------------------------------

# see also http://sldn.softlayer.com/reference/datatypes/SoftLayer_Billing_Item

FIELDNAMES=('id',
            'parentId',
            'associatedBillingItemId',
            
            'categoryCode',
            'description',
            'notes',

            'resourceName',
            'resourceTableId',

            'orderItemId',

            'serviceProviderId',

            'laborFee',
            'laborFeeTaxRate',

            'oneTimeFee',
            'oneTimeFeeTaxRate',

            'setupFee',
            'setupFeeTaxRate',

            'recurringFee',
            'recurringFeeTaxRate',
            
            'hoursUsed',
            'currentHourlyCharge',
            'hourlyRecurringFee',

            'recurringMonths',

            'allowCancellationFlag',

            'hostName',
            'domainName',

            'createDate',
            'modifyDate',
            'cycleStartDate',
            'cancellationDate',
            'lastBillDate',
            'nextBillDate',
            )
HEADER = dict([ (val,val) for val in FIELDNAMES ])  

fname = 'slmon' + datetime.datetime.now().strftime("%y%m%d%H%M%S") + '.csv'

# ----------------------------------------------------------------------

try:
    master_account = client['Account']
    
    print("## Account information ##") 
    user_mask="id, firstName, lastName, email"
    account_info = master_account.getObject(mask=user_mask)
    print(account_info)
    
    print("## Users ##");
    for user in Users(client):
        print("id:%d, %s" % (user['id'], user['username']))

    print("## Billing items ##")
    billingItems = []
    for b in BillingItems(client):
        billingItems.append(b)
        #writer.writerow(b)
        #print(json.dumps(b, sort_keys=True, indent=4))
    
    # Output
    print('Write to ' + fname)
    with open(fname, mode='w') as f:
        writer = csv.DictWriter(f, FIELDNAMES, extrasaction='raise') # ignore/raise
        billingItems.insert(0, HEADER)
        writer.writerows(billingItems)

except SoftLayer.SoftLayerAPIError as e:
    logger.error("Unable to retrieve account information faultCode%s, faultString=%s"
          % (e.faultCode, e.faultString))
    exit(1)
