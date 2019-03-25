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
    def insert(self):
        return BaseObjectHandler.insert(self)
 
    @with_validator([F('id', T_INT), F('info'), F('name'), F('parentid', T_INT)])
    def update(self):
        return BaseObjectHandler.update(self)
 
