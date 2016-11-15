# coding: utf-8
import os, sys
import random, hashlib
from zbase.web import core
import session2
import config
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


class BaseHander (core.Handler):
    def initial(self):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        self.ses = None
        sid = self.get_cookie('sid')
        if sid: 
            sescls = get_session(config['SESSION']['type'])
            self.ses = sescls(config['SESSION']['server'], sid=sid,
                    expire=config['SESSION']['expire'])


    
    def finish(self):
        if self.ses and self.ses.sid:
            self.ses.save()
            self.set_cookie('sid', self.ses.sid)

    def create_sesson(self):
        sescls = get_session(config['SESSION']['type'])
        self.ses = sescls(config['SESSION']['server'], expire=config['SESSION']['expire'])

    def succ(self, data=None):
        obj = {'ret':OK}
        if data:
            obj['data'] = data
        s = json.dumps(obj, separators=(',', ':'))
        log.info('succ: %s', s)
        self.write(s)

    def fail(self, errstr=u'internal error'):
        obj = {'ret':ERR, 'error':errstr}
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




