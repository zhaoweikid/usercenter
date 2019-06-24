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


# 未认证
STATUS_NOAUTH = 1
# 正常
STATUS_OK  = 2
# 封禁
STATUS_BAN = 3
# 删除
STATUS_DEL = 4


def check_perm(perms):
    def f(func):
        def _(self, *args, **kwargs):
            if self.ses.get('isadmin', 0):
                return func(self, *args, **kwargs)

            p = self.ses.get('allperm')
            if not p:
                return self.fail(ERR_PERM)
            allperms = set(p)
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
        if name != 'query':
            return httpcore.NotFound()

        try:
            code, ret = self.query()

            if code == OK:
                return self.succ(ret)
            else:
                return self.fail(code, ret)
        except:
            log.error(traceback.format_exc())
            return self.fail(ERR_INTERNAL)

    def POST(self, name=None):
        log.warn('====== POST %s %s ======', self.req.path, self.req.query_string)
        
        try:
            func = getattr(self, name, None)
            if not func:
                return httpcore.NotFound()
            code, ret = func()

            if code == OK:
                return self.succ(ret)
            else:
                return self.fail(code, ret)
        except:
            log.error(traceback.format_exc())
            return self.fail(ERR_INTERNAL)
       
    def fail(self, ret, debug=''):
        advance.APIHandler.fail(self, ret, errstr[ret], debug)



class BaseObjectHandler (BaseHandler):
    def _convert_data(self, data):
        def _convert_row(row):
            for k in ['id', 'userid', 'groupid', 'roleid', 'permid', 'parentid']:
                if k in row:
                    row[k] = str(row[k])

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
    def get(self):
        xid = self.data.get('id')
        with get_connection(self.dbname) as conn:
            ret = conn.select_one(self.table, where={'id':xid})
            if ret:
                self._convert_data(ret)
            return OK, ret


    #@with_validator([F('page',T_INT,default=1), F('pagesize',T_INT,default=20)])
    # 必须自己定义装饰器来限制参数
    def get_list(self):
        where = {}
        for k in self.data:
            if k in ['page', 'pagesize']:
                continue
            v = self.data.get(k)
            if not v:
                continue
            if isinstance(v, (list,tuple)):
                where[k] = ('in', v)
            else:
                where[k] = v

        return self.get_data(self.data['page'], self.data['pagesize'], where)
 
    
    def get_data(self, page, pagesize, where=None):
        log.debug('list page:%s pagesize:%s', str(page), str(pagesize))
        retdata = {'page':page, 'pagesize':pagesize, 'pagenum':0}
        with get_connection(self.dbname) as conn:
            sql = conn.select_sql(self.table, where=where)
            ret = conn.select_page(sql, page, pagesize)
            if ret.pagedata.data:
                self._convert_data(ret.pagedata.data)

                retdata['pagenum'] = ret.pages
                retdata['data'] = ret.pagedata.data

        return OK, retdata


    def create(self):
        data = self.validator.data
        t = int(time.time())
        for k in ['ctime']:
            if k not in data:
                data[k] = t
                
        with get_connection(self.dbname) as conn:
            if not data.get('id'):
                data['id'] = createid.new_id64(conn=conn)

            ret = conn.insert(self.table, data)
            if ret == 1:
                return OK, {'id':str(data['id'])}
            else:
                return ERR_DATA, 'insert error'

    def modify(self):
        data = copy.copy(self.data)
        log.debug('data:%s', self.data)
        if not data:
            return ERR_PARAM, 'param error'

        xid = data.pop('id')
        if isinstance(xid, (list, tuple)):
            xid = ('in', xid)

        if not data:
            return ERR_PARAM, 'no data'

        with get_connection(self.dbname) as conn:
            ret = conn.update(self.table, data, where={'id':xid})
            if ret >= 1:
                data['_rows'] = ret
                if not isinstance(xid, (list, tuple)):
                    data['id'] = str(xid)
                return OK, data
            else:
                return ERR_DATA, 'update error'

    def query(self):
        data = self.req.input()
        if data.get('id'):
            return self.get()
        else:
            return self.get_list()

    def delete(self, xid):
        xid = int(xid)
        with get_connection(self.dbname) as conn:
            ret = conn.delete(self.table, where={'id':xid})
            return OK, ret


