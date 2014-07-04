#!/usr/bin/env python3
#                                        -*- coding:utf-8 -*-
#
#  slcrooge.py: Get Billing information utility
#  Created by NAKAJIMA Takaaki 
#  Last modified: Jul. 4, 2014.
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
import csv
import datetime
from decimal import Decimal as Decimal
import dateutil.parser
import SoftLayer
import json

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
        self.client = client
        self.offset = 0
        self.limit = limit
        self.fetched = []
        
    def concrete_fetch(self):
        u"""MUST be implemented in inherited class"""
        # self.fetch_method に適切な pagenate メソッドを設定
        raise NotImpementedError("Not implemented yet.")
    
    def fetch(self):
        items = self.concrete_fetch()
        self.offset += self.limit
        return items
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if len(self.fetched) < 1:
            self.fetched = self.fetch()
            logging.debug(self.__class__.__name__ + ' has been fetched.')
            if len(self.fetched) < 1: # No residual items
                raise StopIteration
        item = self.fetched.pop()
        return self.cast_hook(item)
    
    def cast_hook(self, obj):
        u"""You can override to cast an object"""
        return obj

class DictStore():
    def __init__(self, d):
        for k, v in d.items():
            self.add(k, v)
    
    def add(self, key, value):
        self.__dict__[key] = value
    
    def header_list(self):
        u"""Should be implemented in inherited class"""
        return []
    
    def to_a(self):
        lst = []
        for k in self.header_list():
            v = ''
            if k in self.__dict__:
                v = self.__dict__[k]
            lst.append(v)
        return lst

class Users(IterableItems):
    u"""List of User_Customer"""
    def concrete_fetch(self):
        return self.client['Account'].getUsers(offset=self.offset, limit=self.limit)

class VirtualGuests(IterableItems):
    u"""List of Virtual_Guest"""
    def concrete_fetch(self):
        return self.client['Account'].getVirtualGuests(offset=self.offset, limit=self.limit)

class BillingItems(IterableItems):
    u"""List of Billing_Item"""
    def concrete_fetch(self):
        return client['Account'].getAllBillingItems(offset=self.offset, limit=self.limit)

class PaidBillingItems(IterableItems):
    u"""List of Billing_Items of Past Billing Invoice"""
    def __init__(self, client, invoice_id, limit=10):
        super(PaidBillingItems, self).__init__(client, limit)
        self.invoice_id = invoice_id

    def concrete_fetch(self):
        return self.client['Billing_Invoice'].getItems(id=self.invoice_id, limit=self.limit, offset=self.offset)

class BillingInvoices(IterableItems):
    u"""List of Billing_Invoices"""
    def concrete_fetch(self):
        return client['Account'].getInvoices(offset=self.offset, limit=self.limit)

# ----------------------------------------------------------------------

def str2date(str):
    return dateutil.parser.parse(str)

# ----------------------------------------------------------------------

timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")

try:
    client = SoftLayer.Client()
    
    print("## Account information ##") 
    user_mask="id, firstName, lastName, email"
    account_info = client['Account'].getObject(mask=user_mask)
    print(account_info)
    
    print("## Users ##");
    for user in Users(client):
        print("id:%d, %s" % (user['id'], user['username']))
    
    print("## Paid Billing Invoices ##")
    invoices = []
    for i in BillingInvoices(client):
        invoice_id = i['id']
        with open('slcrooge-' + str(invoice_id) + '.json', mode='w') as f:
            #billing_items = []
            for b in PaidBillingItems(client, invoice_id):
                #billing_items.append(b)
                json.dump(b, f, indent=2)
    
    # MEMO: client['Billing_Invoice'].getObject(id=2638314)
    # client['Billing_Invoice'].getItems(id=2638314)

    print("## Next Billing items ##")
    billingItems = []
    for b in BillingItems(client):
#        billingItems.append(b)
        print(json.dumps(b, sort_keys=True, indent=4))
#    save_csv('slcrooge-latest' + timestamp + '-items.csv', billingItems,
#             header=BillingItem.header_list())  

except SoftLayer.SoftLayerAPIError as e:
    logging.error("Unable to retrieve account information faultCode=%s, faultString=%s"
          % (e.faultCode, e.faultString))
    exit(1)
