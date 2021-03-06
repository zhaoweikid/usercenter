# coding: utf-8
import os, sys
import json, random, hashlib
import time
import copy
from zbase3.web import core
from zbase3.web.validator import *
from zbase3.base.dbpool import get_connection
from zbase3.utils import createid
import logging
from userbase import *

class Group (BaseObjectHandler):
    dbname = 'usercenter'
    table = 'groups'

    @with_validator([F('name'), F('info'), F('parentid', T_INT)])
    def create(self):
        return BaseObjectHandler.create(self)
 
    @with_validator([F('id', T_INT), F('info'), F('name'), F('parentid', T_INT)])
    def modify(self):
        return BaseObjectHandler.modify(self)

    @with_validator([
        F('page',T_INT,default=1), 
        F('pagesize',T_INT,default=20),
        F('name'), 
        F('ctime', T_DATETIME), 
    ])
    def get_list(self):
        return BaseObjectHandler.get_list(self)
 
