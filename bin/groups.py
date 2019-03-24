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

    def GET(self, name):
        try:
            ret = None
            if name == 'q':
                ret = self.get_arg()
            elif name == 'list':
                ret = self.get_list_arg()
            else:
                self.fail(ERR_PARAM, 'url %s not found' % (name))
                return

            self.succ(ret)
        except Exception as e:
            self.fail(ERR_ACTION, str(e))

    
    def POST(self, name):
        try:
            data = self.validator.data
            ret = None
            if name == 'add':
                ret = self.insert(data)
            elif name == 'mod':
                data2 = copy.copy(data)
                data2.pop('id')
                ret = self.update(int(data['id']), data2)
            elif name == 'del':
                ret = self.delete(int(data['id']))
            else:
                self.fail(ERR_PARAM, 'url %s not found' % (name))
                return

            self.succ(ret)
        except Exception as e:
            self.fail(ERR_ACTION, str(e))

 
