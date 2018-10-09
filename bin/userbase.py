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


