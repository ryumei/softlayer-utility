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
    def define_fetch_method(self):
        self.fetch_method = self.client['Account'].getUsers

class VirtualGuests(IterableItems):
    u"""List of Virtual_Guest"""
    def define_fetch_method(self):
        self.fetch_method = self.client['Account'].getVirtualGuests

class BillingItems(IterableItems):
    u"""List of Billing_Item"""
    def define_fetch_method(self):
        self.fetch_method = client['Account'].getAllBillingItems
        # Retrieve the billing items that will be on an account's next invoice.
    def cast_hook(self, obj):
        return BillingItem(obj)        

class PaidBillingItems(IterableItems):
    u"""List of Billing_Items of Past Billing Invoice"""
    def __init__(self, client, invoice_id, limit=10):
        super(PaidBillingItems, self).__init__(client, limit)
        self.invoice_id = invoice_id

    def define_fetch_method(self):
        self.fetch_method = client['Billing_Invoice'].getItems
    
    def fetch(self):
        items = self.fetch_method(id=self.invoice_id, limit=self.limit, offset=self.offset)
        self.offset += self.limit
        return items    
    
    def cast_hook(self, obj):
        #print(json.dumps(obj, sort_keys=True, indent=2))
        return obj
        #TODO# return BillingItem(obj)

class BillingInvoices(IterableItems):
    u"""List of Billing_Invoices"""
    def __init__(self, client, limit=10):
        super(BillingInvoices, self).__init__(client, limit)
        self.mask = ','.join(BillingInvoice.header_list())

    def define_fetch_method(self):
        self.fetch_method = client['Account'].getInvoices
    
    def cast_hook(self, obj):
        return BillingInvoice(obj)

# --------------------------------------------------------------

# see also http://sldn.softlayer.com/reference/datatypes/SoftLayer_Billing_Item

class BillingItem(DictStore):
    def __init__(self, d):
        super(BillingItem, self).__init__(d)
        self.createDate       = str2date(d['createDate'])
        self.modifyDate       = str2date(d['modifyDate'])
        self.cycleStartDate   = str2date(d['cycleStartDate'])
        self.cancallationDate = str2date(d['cancellationDate'])
        self.lastBillDate     = str2date(d['lastBillDate'])
        self.nextBillDate     = str2date(d['nextBillDate'])
        
    @classmethod
    def header_list(cls):
        return [ 'id', 'parentId', 'associatedBillingItemId',
                 'categoryCode', 'description', 'notes',
                 'resourceName',      'resourceTableId',
                 'orderItemId',
                 'serviceProviderId',
                 'laborFee',          'laborFeeTaxRate',                 
                 'oneTimeFee',        'oneTimeFeeTaxRate',
                 'setupFee',          'setupFeeTaxRate',
                 'recurringFee',      'recurringFeeTaxRate',
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
                 'nextBillDate', ]

class BillingInvoice(DictStore):
    def __init__(self, d):
        super(BillingInvoice, self).__init__(d)
        
        self.createDate = str2date(d['createDate'])
        self.closedDate = str2date(d['closedDate'])
        self.modifyDate = str2date(d['modifyDate'])        
        if 'startingBalance' in d:
            self.startingBalance = Decimal(d['startingBalance'])
        else:
            self.startingBalance = Decimal(0)   # TODO: determine default value
        self.endingBalance   = Decimal(d['endingBalance'])
    
    @classmethod
    def header_list(cls):
        return [ 'accountId', 'id',
                 'createDate', 'closedDate', 'modifyDate',
                 'startingBalance', 'endingBalance', 'taxStatusId', 'taxTypeId',
                 'statusCode', 'state', 'typeCode' ]

# ----------------------------------------------------------------------

def str2date(str):
    return dateutil.parser.parse(str)

def save_csv(filename, items, header=[]):
    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f) #, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        try:
            writer.writerow(header)
            col = 0
            for i in items:
                col += 1
                writer.writerow(i.to_a())
        except csv.Error as e:
            logging.error('file %s: line %d: %s' % (filename, col, e))
            exit(1)

# ----------------------------------------------------------------------

timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")

try:
    client = SoftLayer.Client()
    
    master_account = client['Account']
    
    print("## Account information ##") 
    user_mask="id, firstName, lastName, email"
    account_info = master_account.getObject(mask=user_mask)
    print(account_info)
    
#    print("## Users ##");
#    for user in Users(client):
#        print("id:%d, %s" % (user['id'], user['username']))
    
    print("## Paid Billing Invoices ##")
    invoices = []
    for i in BillingInvoices(client):
        invoices.append(i)
        billing_items = []
        with open('slcrooge-' + str(i.id) + '.json', mode='w') as f:
            for b in PaidBillingItems(client, i.id):
                billing_items.append(b)
                json.dump(b, f, indent=2)
    
    # MEMO: client['Billing_Invoice'].getObject(id=2638314)
    # client['Billing_Invoice'].getItems(id=2638314)

    print("## Next Billing items ##")
    billingItems = []
    for b in BillingItems(client):
        billingItems.append(b)
        #print(json.dumps(b, sort_keys=True, indent=4))
    save_csv('slcrooge-' + timestamp + '-items.csv', billingItems,
             header=BillingItem.header_list())  

    

except SoftLayer.SoftLayerAPIError as e:
    logging.error("Unable to retrieve account information faultCode=%s, faultString=%s"
          % (e.faultCode, e.faultString))
    exit(1)
