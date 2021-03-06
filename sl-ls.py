#!/usr/bin/env python3
#                                        -*- coding:utf-8 -*-
#
#  sl-ls.py: get information utility
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

import SoftLayer
client = SoftLayer.Client()

class IterableItems:
    u"""Pagenate されているリストを全体を回せるようにする"""
    
    def __init__(self, client, limit=10):
        self.master_account = client['Account']
        self.offset = 0
        self.limit = limit
        self.define_fetch_method()
        self.fetched = self.fetch()
        
    def define_fetch_method(self):
        u"""継承側クラスで実装すること"""
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

# --------------------------------------------------------------

try:
    master_account = client['Account']

    print("## Account information ##") 
    user_mask="id, firstName, lastName, email"
    account_info = master_account.getObject(mask=user_mask)
    print(account_info)
    
    # all child users
    #for user in master_account.getUsers(limit=10, offset=0):
    print("## Users ##");
    for user in Users(client):
        print("id:%d, %s" % (user['id'], user['username']))
       
    # Virtual guest OSes
    # for vg in client['Account'].getVirtualGuests(limit=10, offset=0):
    print("## Virtual guests ##");
    for vg in VirtualGuests(client):
        print("AccountId=%s, ID=%d, hostname=%s"
              % (vg['accountId'], vg['id'], vg['hostname']))
    
    print("## Instances ##");
    cci_manager = SoftLayer.CCIManager(client)
    for cci in cci_manager.list_instances():
        print("FQDN=%s, IP_addrs=%s, %s" 
              % (cci['fullyQualifiedDomainName'], cci['primaryIpAddress'], cci['primaryBackendIpAddress']))
       
    print("## Billing items ##")
    billing_mask = "id, parentId, description, currentHourlyCharge"
    print(master_account.getAllBillingItems(mask=billing_mask))

except SoftLayer.SoftLayerAPIError as e:
    print("Unable to retrieve account information faultCode%s, faultString=%s"
          % (e.faultCode, e.faultString))
    exit(1)
