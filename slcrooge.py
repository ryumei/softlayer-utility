#!/usr/bin/env python3
#                                        -*- coding:utf-8 -*-
#
#  slcrooge.py: Get Billing information utility
#  Created by NAKAJIMA Takaaki 
#  Last modified: Apr 16, 2014.
#
#  Require:
#    Python v3
#    python-softlayer (via pip)
#    python-dateutil (via pip)
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

# ----------------------------------------------------------------------

# Logging

stream_log = logging.StreamHandler()
stream_log.setLevel(logging.INFO)
stream_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

file_log = logging.FileHandler(filename='slcrooge.log')
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

logging.getLogger().addHandler(stream_log)
logging.getLogger().addHandler(file_log)

logging.getLogger().setLevel(logging.DEBUG)

# ----------------------------------------------------------------------

class IterableItems:
    u"""Iterator for Pagenated list"""
    
    def __init__(self, client, limit=10):
        self.master_account = client['Account']
        self.offset = 0
        self.limit = limit
        self.mask = ''
        self.define_fetch_method()
        self.fetched = []
        
    def define_fetch_method(self):
        u"""MUST be implemented in inherited class"""
        # self.fetch_method に適切な pagenate メソッドを設定
        raise NotImpementedError("Not implemented yet.")

    #def set_mask(self, mask):
    #    self.mask = mask

    def fetch(self):
        if (self.mask != ''):
            items = self.fetch_method(limit=self.limit, offset=self.offset, mask=self.mask)
        else:
            items = self.fetch_method(limit=self.limit, offset=self.offset)
        self.offset += self.limit
        return items
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if len(self.fetched) < 1:
            self.fetched = self.fetch()
            logging.debug(self.__class__.__name__ + ' has been fetched.')
            if len(self.fetched) < 1: # No redisual items
                raise StopIteration
        item = self.fetched.pop()
        return item

class Users(IterableItems):
    u"""List of User_Customer"""
    def define_fetch_method(self):
        self.fetch_method = self.master_account.getUsers

class VirtualGuests(IterableItems):
    u"""List of Virtual_Guest"""
    def define_fetch_method(self):
        self.fetch_method = self.master_account.getVirtualGuests

class BillingItems(IterableItems):
    u"""List of Billing_Item"""
    def define_fetch_method(self):
        self.fetch_method = master_account.getAllBillingItems

from decimal import Decimal as Decimal

class BillingInvoice():
    def __init__(self, d):
        self.accountId  = d['accountId']
        self.id         = d['id']
        self.createDate = str2date(d['createDate'])
        self.closedDate = str2date(d['closedDate'])
        self.modifyDate = str2date(d['modifyDate'])
        self.startingBalance = Decimal(d['startingBalance'])
        self.endingBalance   = Decimal(d['endingBalance'])
        self.taxStatusId = d['taxStatusId']
        self.taxTypeId = d['taxTypeId']
        self.statusCode = d['statusCode']
        self.state = d['state']
        self.typeCode = d['typeCode']

class BillingInvoices(IterableItems):
    u"""List of Billing_Invoices"""
    def __init__(self, client, limit=10):
        super(BillingInvoices, self).__init__(client, limit)
        self.mask = 'accountId,id,createDate,closedDate,modifyDate,startingBalance,endingBalance,taxStatusId,taxTypeId,statusCode,state,typeCode'

    def define_fetch_method(self):
        self.fetch_method = master_account.getInvoices

import dateutil.parser

def str2date(str):
    return dateutil.parser.parse(str)
    # [WORKARROUND]
    #str = re.sub(r'(\+\d\d):(\d\d)$', '\\1\\2', str)
    #return datetime.datetime.strptime(str, '%Y-%m-%dT%H:%M:%S%z')


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

fname = 'slcrooge-' + datetime.datetime.now().strftime("%y%m%d%H%M%S") + '.csv'

# ----------------------------------------------------------------------

try:
    client = SoftLayer.Client()
    
    master_account = client['Account']
    
    print("## Account information ##") 
    user_mask="id, firstName, lastName, email"
    account_info = master_account.getObject(mask=user_mask)
    print(account_info)
    
    #print("## Users ##");
    #for user in Users(client, limit=20):
    #    print("id:%d, %s" % (user['id'], user['username']))

    # https://%SL_USERNAME%:%SL_API_KEY%@api.softlayer.com/rest/v3/SoftLayer_Account/Invoices.json
    invoices = []
    print("Billing Invoices")
    for i in BillingInvoices(client):
        print(json.dumps(i, sort_keys=True, indent=2))
        print(str2date(i['createDate']))
        invoices.append(i)

    #with open('slcrooge-invoices', mode='w') as f:
    #    writer = csv.DictWriter(f, FIELDNAMES, extrasaction='raise') # ignore/raise
    #    
    #    writer.writerows(invoices)


    print("Billing items: -> " + fname)
    billingItems = []
    for b in BillingItems(client):
        billingItems.append(b)
        #writer.writerow(b)
        #print(json.dumps(b, sort_keys=True, indent=4))
    
    # Output
    with open(fname, mode='w') as f:
        writer = csv.DictWriter(f, FIELDNAMES, extrasaction='raise') # ignore/raise
        billingItems.insert(0, HEADER)
        writer.writerows(billingItems)

except SoftLayer.SoftLayerAPIError as e:
    logging.error("Unable to retrieve account information faultCode=%s, faultString=%s"
          % (e.faultCode, e.faultString))
    exit(1)
