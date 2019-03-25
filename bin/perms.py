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

# 权限命名规则
# xxxx 为对应功能模块名称
# 查看 xxxx_view
# 创建 xxxx_create
# 修改 xxxx_mod (大多数时候, mod可以包含create和del，不需要create和del权限)
# 删除 xxxx_del
# 其他 xxxx_abc

class Perm (BaseObjectHandler):
    dbname = 'usercenter'
    table = 'perms'

    @check_perm(['perm_view'])
    def GET(self, name):
        return BaseObjectHandler.GET(self, name)

    @check_perm(['perm_mod'])
    def POST(self, name):
        return BaseObjectHandler.POST(self, name)

    @with_validator([F('name'), F('info')])
    def insert(self):
        return BaseObjectHandler.insert(self)
 
    @with_validator([F('id', T_INT), F('name'), F('info')])
    def update(self):
        return BaseObjectHandler.update(self)
 
class Role (BaseObjectHandler):
    dbname = 'usercenter'
    table = 'roles'

    @check_perm(['perm_view'])
    def GET(self, name):
        return BaseObjectHandler.GET(self, name)

    @check_perm(['perm_mod'])
    def POST(self, name):
        return BaseObjectHandler.POST(self, name)

    @with_validator([F('name'), F('info')])
    def insert(self):
        return BaseObjectHandler.insert(self)
 
    @with_validator([F('id', T_INT), F('name'), F('info')])
    def update(self):
        return BaseObjectHandler.update(self)
 
