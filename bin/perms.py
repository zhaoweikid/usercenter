# coding: utf-8
import os, sys
import json, random, hashlib
import time
import copy
from zbase3.web import core
from zbase3.web.validator import *
from zbase3.base.dbpool import get_connection, DBFunc
from zbase3.utils import createid
import logging
import config
from userbase import *

# 权限命名规则
# xxxx 为对应功能模块名称
# 查看 xxxx_view
# 创建 xxxx_create
# 修改 xxxx_mod (大多数时候, mod可以包含create和del，不需要create和del权限)
# 删除 xxxx_del
# 其他 xxxx_abc

class Perm (BaseObjectHandler):
    dbname = config.DBNAME
    table = 'perms'

    @check_perm(['perm_view'])
    def GET(self, name):
        return BaseObjectHandler.GET(self, name)

    @check_perm(['perm_mod'])
    def POST(self, name):
        return BaseObjectHandler.POST(self, name)

    @with_validator_dict([F('name'), F('info')])
    def create(self):
        return BaseObjectHandler.create(self)
 
    @with_validator_dict([
        F('id', T_LIST, subs=[
            F("_", T_INT),
        ]), 
        F('name'), F('info')
    ])
    def modify(self):
        return BaseObjectHandler.modify(self)

    @with_validator_dict([
        F('page',T_INT,default=1), 
        F('pagesize',T_INT,default=20),
        F('name'), 
        F('ctime', T_DATETIME), 
    ])
    def get_list(self):
        return BaseObjectHandler.get_list(self)
 
 
class Role (BaseObjectHandler):
    dbname = config.DBNAME
    table = 'roles'

    @check_perm(['perm_view'])
    def GET(self, name):
        return BaseObjectHandler.GET(self, name)

    def get(self, xid):
        sql = 'select p.id as id,p.name as name,p.info as info from perms p, role_perm rp where rp.roleid=%d and rp.permid=p.id' % (int(xid))
        with get_connection(self.dbname) as conn:
            ret = conn.select_one(self.table, where={'id':xid})
            if ret:
                self._convert_data(ret)

                ret['perm'] = []

                perms = conn.query(sql)
                if perms:
                    ret['perm'] = perms 


            return OK, ret


    def get_data(self, page, pagesize, where=None):
        retcode, retdata = BaseObjectHandler.get_data(self, page, pagesize, where)
        if retcode == OK and retdata and retdata['data']:
            roleids = ','.join([ str(x['id']) for x in retdata['data'] ])
        
            sql = 'select p.id as id,p.name as name,p.info as info,rp.roleid as roleid from perms p, role_perm rp where rp.roleid in (%s) and rp.permid=p.id' % \
                (roleids)

            with get_connection(self.dbname) as conn:
                ret = conn.query(sql)
                if ret:
                    roledict = {}
                    for row in ret:
                        k = str(row['roleid'])
                        if k not in roledict:
                            roledict[k] = [row]
                        else:
                            roledict[k].append(row)
                        row.pop('roleid')

                    for row in retdata['data']:
                        row['perm'] = roledict.get(row['id'], [])
                else:
                    for row in retdata['data']:
                        row['perm'] = []

        return retcode, retdata

 
    @with_validator_dict([
        F('id', T_LIST, must=True, subs=[
            F('_', T_INT),
        ]), 
        F('permid', T_INT, must=True) 
    ])
    def perm_alloc(self):
        permid = self.data.get('permid')
        
        values = []
        if isinstance(permid, (list, tuple)):
            for p in permid:
                values.append({'permid':p, 'roleid':self.data.get('id'), 'ctime':DBFunc('now()'), 'utime':DBFunc('now()')})
        else:
            values.append({'permid':permid, 'roleid':self.data.get('id'), 'ctime':DBFunc('now()'), 'utime':DBFunc('now()')})

        with get_connection(self.dbname) as conn:
            for value in values:
                value['id'] = createid.new_id64(conn=conn)
                ret = conn.insert('role_perm', value)

        return OK, {'rows':len(values)}

    @with_validator_dict([
        F('id', T_LIST, subs=[
            F('_', T_INT)
        ]), 
        F('permid', T_INT), 
        F('roleperm_id', T_INT)  
    ])
    def perm_cancel(self):
        roleid = self.data.get('id')
        permid = self.data.get('permid')
        roleperm_id = self.data.get('roleperm_id')
        
        where = None
        if permid and roleid:
            if isinstance(permid, (list, tuple)):
                where = {'permid':('in', permid), 'roleid':self.data.get('id')}
            else:
                where = {'permid':permid, 'roleid':self.data.get('id')}
        elif roleperm_id:
            if isinstance(roleperm_id, (list, tuple)):
                where = {'id', ('in', roleperm_id)}
            else:
                where = {'id': roleperm_id}
        else:
            return ERR_PARAM, 'param error'

        ret = None
        with get_connection(self.dbname) as conn:
            ret = conn.delete('role_perm', where) 

        return OK, {'rows': ret}



    @check_perm(['perm_mod'])
    def POST(self, name):
        return BaseObjectHandler.POST(self, name)

    @with_validator_dict([
        F('name'), F('info')
    ])
    def create(self):
        return BaseObjectHandler.create(self)
 
    @with_validator_dict([
        F('id', T_LIST, subs=[
            F('_', T_INT)
        ]), 
        F('name'), F('info')
    ])
    def modify(self):
        return BaseObjectHandler.modify(self)
 
    @with_validator_dict([
        F('page',T_INT,default=1), 
        F('pagesize',T_INT,default=20),
        F('name'), 
        F('ctime', T_DATETIME), 
    ])
    def get_list(self):
        return BaseObjectHandler.get_list(self)


