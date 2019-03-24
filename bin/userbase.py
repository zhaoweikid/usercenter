# coding: utf-8
import os, sys
import random, hashlib
from zbase3.web import core, advance
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

errstr = {
    OK: '成功',
    ERR: '失败',
    ERR_USER: '用户错误',
    ERR_PARAM: '参数错误',
    ERR_AUTH: '认证失败',
    ERR_ACTION: '操作失败',
    ERR_DATA: '数据错误',
    ERR_PERM: '权限错误',
}

def create_password(passwd, salt=None):
    if salt is None:
        salt = random.randint(1, 1000000)
    saltstr = '%06d' % salt 
    tmp = passwd+saltstr
    return 'sha1$%s$%s' % (salt, hashlib.sha1(tmp.encode('utf-8')).hexdigest())

class BaseHandler (advance.APIHandler):
    session_conf = config.SESSION

    def GET(self, name):
        try:
            func = getattr(self, name)
            return func()
        except:
            log.info(traceback.format_exc())
            return self.failed()

    def POST(self, name):
        return self.GET(name)

    def fail(self, ret, debug=''):
        advance.APIHandler.fail(self, ret, errstr[ret], debug)



class BaseObjectHandler (BaseHandler):

    @with_validator([F('id',T_INT)])
    def get_arg(self):
        data = self.validator.data

        return self.get(data['id'])
 
    def get(self, xid):
        with get_connection(self.db) as conn:
            ret = conn.select(self.table, where={'id':xid})
            return ret


    @with_validator([F('page',T_INT), F('pagesize',T_INT)])
    def get_list_arg(self):
        data = self.validator.data
        
        return self.get_list(data['page'], data['pagesize'])
    
    def get_list(self, page, pagesize):
        retdata = {'page':page, 'pagesize':pagesize, 'pagenum':0}
        with get_connection(self.db) as conn:
            sql = conn.select_sql(self.table)
            ret = conn.select_page(sql, page, pagesize)
            if ret:
                retdata['pagenum'] = ret.pages
                retdata['data'] = ret.pagedata.data

        return retdata


    def insert(self, data):
        with get_connection(self.db) as conn:
            ret = conn.insert(self.table, data)
            return ret

    def update(self, xid, data):
        with get_connection(self.db) as conn:
            ret = conn.update(self.table, data, where={'id':xid})
            return ret


    def delete(self. xid):
        with get_connection(self.db) as conn:
            ret = conn.delete(self.table, where={'id':xid})
            return ret

    
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



