# coding: utf-8
import os, sys
from zbase.web import core
import logging

log = logging.getLogger()

OK  = 0
ERR = -1

class BaseHander (core.Handler):
    def initial(self):
        self.set_headers({'Content-Type': 'application/json; charset=UTF-8'})
        self.ses = None

    
    def finish(self):
        pass


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


