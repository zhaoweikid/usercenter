# coding: utf-8
import os, sys
import random, hashlib
from zbase.web import core
from zbase.web import session2
import config
import json
import logging

log = logging.getLogger()

OK  = 0
ERR = -1

def create_password(passwd, salt=None):
    if salt is None:
        salt = random.randint(1, 1000000)
    saltstr = '%06d' % salt 
    return 'sha1$%s$%s' % (salt, hashlib.sha1(passwd+saltstr).hexdigest())

def get_session(classname):
    return getattr(session2, classname)


def check_login(f):
    def _(self, *args, **kwargs):
        if not self.ses or not self.ses['uid']:
            return self.fail('please login')
        f(self, *args, **kwargs)
    return _


class BaseHandler (core.Handler):
    def initial(self):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        self.ses = None
        sid = self.get_cookie('sid')
        log.info('sid:%s', sid)
        if sid: 
            sescls = get_session(config.SESSION['type'])
            self.ses = sescls(sid, server=config.SESSION['server'][0],
                    expire=config.SESSION['expire'])

        #if not sid and self.req.path != '/v1/user/register':
        #    return self.fail('please login first')

    def finish(self):
        if self.ses and self.ses.sid:
            self.ses.save()
            self.set_cookie('sid', self.ses.sid)

    def create_session(self):
        log.debug('session config: %s', config.SESSION)
        sescls = get_session(config.SESSION['type'])
        self.ses = sescls(server=config.SESSION['server'][0], expire=config.SESSION['expire'])
        return self.ses

    def succ(self, data=None):
        obj = {'ret':OK}
        if data:
            obj['data'] = data
        s = json.dumps(obj, separators=(',', ':'))
        log.info('succ: %s', s)
        self.write(s)

    def fail(self, errstr=u'internal error'):
        obj = {'ret':ERR, 'err':errstr}
        s = json.dumps(obj, separators=(',', ':'))
        log.info('failed: %s', s)
        self.write(s)

    def get(self, name):
        try:
            func = getattr(self, name)
            return func()
        except:
            log.info(traceback.format_exc())
            return self.failed()

    def post(self, name):
        return self.get(name)




