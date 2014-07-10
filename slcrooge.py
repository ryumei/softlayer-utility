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
file_log.setLevel(logging.INFO)
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

def getAccount(client):
    return client['Account'].getObject(mask="id, firstName, lastName, email")

def getUsers(client):
    users = {} # map of users
    for user in IterableItems(client['Account'].getUsers, mask='id, username'):
        users[user['id']] = user
    return users

class BillingItemUserMap():
    u"""Master map of Billing_Item and User_Customer"""
    
    def __init__(self, client):
        self.account_svc = client['Account']
        self.order_svc = client['Billing_Order']
        self.order_item_svc = client['Billing_Order_Item']
        self.map = self.getMap(client)
    
    def getMap(self, client):
        order_svc = client['Billing_Order']
        order_item_svc = client['Billing_Order_Item']
        
        map = {} 
        for order in IterableItems(self.account_svc.getOrders, mask='id, userRecordId'):
            for billing_order_item in IterableItems(self.order_svc.getItems,
                                                    id=order['id'], mask='id'):
                billing_item = self.order_item_svc.getBillingItem(id=billing_order_item['id'],
                                                                  mask='id')
                map[billing_item['id']] = order['userRecordId']
        return map
    
    def getUserId(self, billing_item_id):
        return self.map[billing_item_id]
                
    def exist(self, billing_item_id):
        return billing_item_id in self.map 


class UserInvoice():

    def __init__(self, client, users):
        self.invoice_svc = client['Billing_Invoice']
        self.users = users
        
    def getInvoiceItems(self, invoice_id):
        items = dict.fromkeys(users.keys()) # NOTE: Should NOT USE initializer (shared)
        for k in items.keys():
            items[k] = []
        items['None'] = []
         
        for billing_invoice_item in IterableItems(self.invoice_svc.getItems,
                                                  id=invoice_id, 
                                                  mask=BillingItem.header_as_mask()):
            logging.info('Billing_Invoice:%d Billing_Invoice_Item:%d'
                         % (invoice_id, billing_invoice_item['id']))
            
            billing_item_id = billing_invoice_item['billingItemId']
            if bi_map.exist(billing_item_id):
                user_id = bi_map.getUserId(billing_item_id)
            else:
                logging.warning('No user found for Billing_Invoice_Item:%s'
                                % (str(billing_invoice_item)))
                user_id = 'None'
            items[user_id].append(billing_invoice_item['id'])
            
            #print("%d-%d ordered by %s"
            #      % (invoice_id, billing_invoice_item['billingItemId'], user_id))
        
        return items

#
#   Billing_Invoice_Item <-> Billing_Item
#   Billing_Item <-> 
#   User_Customer <-> Billing_Order
#   Billing_Order <-> Billing_Item
#
#
#

                

# ----------------------------------------------------------------------

#timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")

try:
    client = SoftLayer.Client()
    
    # 1. Build map Billing_Item to User_Customer from Billing_Order
    users = getUsers(client)
    # map of billing_items and users (ordered)
    bi_map = BillingItemUserMap(client)
    
    # 2. Processing each Billing_Invoices
    
    # 2.1. Billing_Invoice
    invoice_mgr = UserInvoice(client, users)
    for invoice in IterableItems(client['Account'].getInvoices, mask='id'):
        logging.info('Billing_Invoice:%d' % (invoice['id']))

        print('Billing_Invoice:%d' % (invoice['id']))        
        
        items = invoice_mgr.getInvoiceItems(invoice['id'])
        for user_id, invoice_items in items.items():
            if user_id in users:
                print("  User_Customer:%s" % (users[user_id]))
            else:
                logging.warning('Unknown user: %s' % ( user_id ))
            # BillingInvoiceItem に変更しないといけない？
            #
            
            for invoice_item in invoice_items:
                #TODO Billing_Invoice_Item id
                print("    Billing_Invoice_Item id:%d" % (invoice_item))
                #print("    Billing_Item:%s" % (invoice_item['id']))
        
        
        
        
    exit(1)
    
    # (ToDo) 3. Latest Billing_Items (without Invoice)
    
###    # User information
###    for user in IterableItems(account_svc.getUsers, mask='id, username'):
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
