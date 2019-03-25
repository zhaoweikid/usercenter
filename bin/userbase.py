# coding: utf-8
import os, sys
import random, hashlib
import time
import datetime
import copy
from zbase3.web import core, advance
from zbase3.web.validator import *
from zbase3.base import dbpool
from zbase3.base.dbpool import get_connection
from zbase3.utils import createid
import config
import json
import logging

log = logging.getLogger()

OK  = 0
ERR = -1
ERR_USER    = -2
ERR_PARAM   = -3
ERR_AUTH    = -4
ERR_ACTION  = -5
ERR_DATA    = -6
ERR_PERM    = -7
ERR_INTERNAL= -8

errstr = {
    OK: '成功',
    ERR: '失败',
    ERR_USER: '用户错误',
    ERR_PARAM: '参数错误',
    ERR_AUTH: '认证失败',
    ERR_ACTION: '操作失败',
    ERR_DATA: '数据错误',
    ERR_PERM: '权限错误',
    ERR_INTERNAL: '内部错误',
}


def check_perm(perms):
    def f(func):
        def _(self, *args, **kwargs):
            allperms = set(self.ses['allperm'])
            s = set(perms) 
            if not s.issubset(allperms):
                return self.fail(ERR_PERM)
            return func(self, *args, **kwargs)
        return _
    return f

def check_admin(func):
    def _(self, *args, **kwargs):
        if not self.ses['isadmin']:
            return self.fail(ERR_PERM)
        return func(self, *args, **kwargs)
    return _

  
def trans_db(key, data):
    if key == 'id':
        return str(data)
    elif key in ['ctime', 'utime'] and isinstance(data, int):
        return str(datetime.datetime.fromtimestamp(data))[:19]  
    return data

dbpool.add_trans(['id','ctime','utime'], trans_db)


def create_password(passwd, salt=None):
    if salt is None:
        salt = random.randint(1, 1000000)
    saltstr = '%06d' % salt 
    tmp = passwd+saltstr
    return 'sha1$%s$%s' % (salt, hashlib.sha1(tmp.encode('utf-8')).hexdigest())

class BaseHandler (advance.APIHandler):
    session_conf = config.SESSION

    def GET(self, name):
        log.warn('====== GET %s %s ======', self.req.path, self.req.query_string)
        try:
            func = getattr(self, name)
            return func()
        except:
            log.error(traceback.format_exc())
            return self.fail(ERR_INTERNAL)

    def POST(self, name):
        log.warn('====== POST %s %s ======', self.req.path, self.req.query_string)
        return self.GET(name)

    def fail(self, ret, debug=''):
        advance.APIHandler.fail(self, ret, errstr[ret], debug)



class BaseObjectHandler (BaseHandler):

    def _convert_data(self, data):
        def _convert_row(row):
            if 'id' in row:
                row['id'] = str(row['id'])

            for k in ['ctime','utime']:
                t = row.get(k)
                if isinstance(t, int):
                    row[k] = str(datetime.datetime.fromtimestamp(t))[:19]  

        if isinstance(data, dict):
            _convert_row(data)
        else:
            for row in data:
                _convert_row(row)



    @with_validator([F('id',T_INT)])
    def get_arg(self):
        data = self.validator.data

        return self.get(data['id'])
 
    def get(self, xid):
        with get_connection(self.dbname) as conn:
            ret = conn.select_one(self.table, where={'id':xid})
            if ret:
                self._convert_data(ret)
            return OK, ret


    @with_validator([F('page',T_INT,default=1), F('pagesize',T_INT,default=20)])
    def get_list_arg(self):
        data = self.validator.data
        return self.get_list(data['page'], data['pagesize'])
    
    def get_list(self, page, pagesize):
        log.debug('list page:%s pagesize:%s', str(page), str(pagesize))
        retdata = {'page':page, 'pagesize':pagesize, 'pagenum':0}
        with get_connection(self.dbname) as conn:
            sql = conn.select_sql(self.table)
            ret = conn.select_page(sql, page, pagesize)
            if ret.pagedata.data:
                self._convert_data(ret.pagedata.data)

                retdata['pagenum'] = ret.pages
                retdata['data'] = ret.pagedata.data

        return OK, retdata


    def insert(self):
        data = self.validator.data
        t = int(time.time())
        for k in ['ctime']:
            if k not in data:
                data[k] = t
                
        with get_connection(self.dbname) as conn:
            if not data.get('id'):
                data['id'] = createid.new_id64(conn=conn)

            ret = conn.insert(self.table, data)
            return OK, ret

    def update(self):
        xid = self.data.get('id')
        data = copy.copy(self.data)
        data.pop('id')
        
        log.debug('data:%s', data)
        if not data:
            return ERR_PARAM, 'param error'

        delks = []
        for k,v in data.items():
            if not v:
                delks.append(k)
        for k in delks:
            data.pop(k)

        with get_connection(self.dbname) as conn:
            ret = conn.update(self.table, data, where={'id':xid})
            return OK, ret

    @with_validator([F('id', T_INT)])
    def delete(self):
        xid = self.data.get('id')
        with get_connection(self.dbname) as conn:
            ret = conn.delete(self.table, where={'id':xid})
            return OK, ret

    
    def GET(self, name):
        log.warn('====== GET %s %s ======', self.req.path, self.req.query_string)
        try:
            ret = None
            if name == 'q':
                code, ret = self.get_arg()
            elif name == 'list':
                code, ret = self.get_list_arg()
            else:
                self.fail(ERR_PARAM, 'url %s not found' % (name))
                return

            if code == OK:
                self.succ(ret)
            else:
                self.fail(code, ret)
        except Exception as e:
            log.error(traceback.format_exc())
            self.fail(ERR_INTERNAL, str(e))

    
    def POST(self, name):
        log.warn('====== POST %s %s ======', self.req.path, self.req.query_string)
        log.debug('name:%s', name)
        try:
            ret = None
            if name == 'add':
                code, ret = self.insert()
            elif name == 'mod':
                code, ret = self.update()
            elif name == 'del':
                code, ret = self.delete()
            else:
                self.fail(ERR_PARAM, 'url %s not found' % (name))
                return

            if code == OK:
                self.succ(ret)
            else:
                self.fail(code, ret)

        except Exception as e:
            log.error(traceback.format_exc())
            self.fail(ERR_INTERNAL, str(e))



