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

import logging, sys, traceback
import csv
import datetime
from decimal import Decimal as Decimal
import dateutil.parser
import SoftLayer
from SoftLayer.utils import NestedDict
import json

# ----------------------------------------------------------------------

# Logging

stream_log = logging.StreamHandler()
stream_log.setLevel(logging.WARNING)
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
    
    def __init__(self, fetch_method, id=None, mask=None, limit=10):
        self.fetch_method = fetch_method
        self.mask = mask # None or comma separated string
        self.id = id
        self.offset = 0
        self.limit = limit
        self.fetched = []
    
    def fetch(self):
        items = self.fetch_method(offset=self.offset, limit=self.limit,
                                  mask=self.mask, id=self.id)
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
        return item

class DictStore():
    def __init__(self, d):
        for k, v in d.items():
            self.add(k, v)
    
    def add(self, key, value):
        self.__dict__[key] = value
    
    @classmethod
    def header_list(self):
        u"""Should be implemented in inherited class"""
        return []
    
    @classmethod
    def header_as_mask(cls):
        return ','.join(cls.header_list())
    
    def to_a(self):
        lst = []
        for k in self.header_list():
            v = ''
            if k in self.__dict__:
                v = self.__dict__[k]
            lst.append(v)
        return lst

# --------------------------------------

class BillingInvoice(DictStore):
    def __init__(self, d):
        super(BillingInvoice, self).__init__(d)
        self.__dict__['createDate'] = str2date(d['createDate'])
        self.__dict__['closedDate'] = str2date(d['closedDate'])
        self.__dict__['modifyDate'] = str2date(d['modifyDate'])
        
    @classmethod
    def header_list(cls):
        return ("id",
                "accountId",

                "statusCode",
                "typeCode",
                "documentsGeneratedFlag",
                
                "startingBalance",
                "endingBalance",
                "taxTypeId",
                "taxStatusId",
                "claimedTaxExemptTxFlag",
                
                "createDate",
                "closedDate",
                "modifyDate",
                )

class BillingItem(DictStore):
    def __init__(self, d):
        super(BillingItem, self).__init__(d)
        self.__dict__['createDate'] = str2date(d['createDate'])
    
    @classmethod
    def header_list(cls):
        return ("id",
                "invoiceId",
                "billingItemId",
                "parentId",
                "associatedInvoiceItemId",
                
                "createDate",
                
                "categoryCode",
                "description",
                "resourceTableId",
                
                "setupFee",
                "setupFeeTaxRate",
                
                "oneTimeFee",
                "oneTimeFeeTaxRate",
                
                "recurringFee",
                "hourlyRecurringFee",
                "recurringFeeTaxRate",
                
                "laborFeeTaxRate",
                "laborFee",
                )

# ----------------------------------------------------------------------

def str2date(str):
    return dateutil.parser.parse(str)

# ----------------------------------------------------------------------

timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")

try:
    client = SoftLayer.Client()
    
#    print("## Account information ##") 
#    account_info = client['Account'].getObject(mask="id, firstName, lastName, email")
#    print(account_info)
    
    # 1. Build map Billing_Item to User_Customer from Billing_Order

    # 1.1. User
    users = {}
    for user in IterableItems(client['Account'].getUsers, mask='id, username'):
        users[user['id']] = user
    
    # 1.2. Billing_Order -> Billing_Order_Item -> Billing_Item
    bi2uid = {} # map of billing_item and user (ordered)
    for order in IterableItems(client['Account'].getOrders, mask='id, userRecordId'):
        for billing_order_item in IterableItems(client['Billing_Order'].getItems,
                                                id=order['id'], mask='id'):
            billing_item = client['Billing_Order_Item'].getBillingItem(id=billing_order_item['id'], mask='id')
            bi2uid[billing_item['id']] = order['userRecordId']
    
    print(bi2uid.keys())
    
    
    # 2. Processing each Billing_Invoices
    
    # Billing_Invoice
    for invoice in IterableItems(client['Account'].getInvoices, mask='id'):
        logging.info('Billing_Invoice:' + str(invoice['id']))
        
        #with open('slcrooge-' + str(invoice['id']) + '.json', mode='w') as f:
        #    bi = client['Billing_Invoice'].getObject(id=invoice['id'])
        #    json.dump(bi, f, indent=2)
        
        items = []
        for billing_invoice_item in IterableItems(client['Billing_Invoice'].getItems,
                                                  id=invoice['id'], mask=BillingItem.header_as_mask()):
            logging.info('Billing_Invoice:' + str(invoice['id']) + ' Billing_Item:' + str(billing_invoice_item['id']))
        
            
            items.append(billing_invoice_item['billingItemId'])
            
            if billing_invoice_item['billingItemId'] in bi2uid:
                user = users[bi2uid[billing_invoice_item['billingItemId']]]
            else:
                logging.warning('No user found for %s' % (str(billing_invoice_item)))
                user = 'None'
            
            print(str(invoice['id']) + '-' + str(billing_invoice_item['billingItemId']) + ' ordered by ' + str(user))
            
            #with open('slcrooge-' + str(invoice['id']) + '-' + str(billing_invoice_item['id']) + '.json', mode='w') as f:
                
            #    json.dump(billing_invoice_item, f, indent=2)
    
        #print(items)
    exit(1)
    
    # (ToDo) 3. Latest Billing_Items (without Invoice)
    
###    # User information
###    for user in IterableItems(client['Account'].getUsers, mask='id, username'):
###        print(json.dumps(user, indent=2))
###        print(client['User_Customer'].getVirtualGuestCount(id=user['id']))
###        
###        billing_items = []
###        
###        # 課金対象となる item ごとに list を作成。
###        kwargs = NestedDict({})
###        kwargs['id'] = user['id']
###        kwargs['mask'] = 'id'
###        
###        for vs in IterableItems(client['User_Customer'].getVirtualGuests, id=user['id'], mask='id'):
###            vs_id = vs['id']
###            
###
###            billing_item_id = int(client['Virtual_Guest'].getBillingItem(id=vs['id'], mask='id')['id'])
###            billing_items.append(billing_item_id)
###            
###            #print(json.dumps(billing_item, indent=2))
###        
###        print(billing_items)
        
except SoftLayer.SoftLayerAPIError as e:
    logging.error("Unable to retrieve account information faultCode=%s, faultString=%s"
          % (e.faultCode, e.faultString))
    traceback.print_exc(file=sys.stdout)
    exit(1)
