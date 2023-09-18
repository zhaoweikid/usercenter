# coding: utf-8
import os, sys
import json, random, hashlib
import time
import copy
from zbase3.web import core, middleware
from zbase3.web.validator import *
from zbase3.web.core import HandlerFinish
from zbase3.base.dbpool import get_connection
from zbase3.utils import createid
import logging
import config
from ucdefines import *

class SignMiddleware:
    def before(self, viewobj, *args, **kwargs):
        '''X-APPID, X-SIGN, X-METHOD'''
        headers = viewobj.req.headers()
        log.debug('headers:%s', headers)
        appid = headers.get(config.OPENSDK_SIGN_VAR['appid'], '')
        sign = headers.get(config.OPENSDK_SIGN_VAR['sign'], '').lower()
        method = headers.get(config.OPENSDK_SIGN_VAR['method'], 'md5')

        log.debug('appid:%s sign:%s', appid, sign)

        with get_connection(viewobj.dbname) as conn:
            app = conn.select_one('apps', where={'appid':appid})
            if not app:
                viewobj.fail(ERR_SIGN, '签名错误, appid错误')
                raise HandlerFinish(500, '签名错误, appid错误')

        s = viewobj.req.postdata() + app['secret'].encode()
        x = hashlib.md5()
        x.update(s)
        sign_result = x.hexdigest()
        log.debug('sign result:%s', sign_result)
        if sign != sign_result:
            log.debug('sign error input:%s compute:%s', sign, sign_result)
            viewobj.fail(ERR_SIGN, '签名错误')
            raise HandlerFinish()

        return

    def after(self, viewobj, *args, **kwargs):
        return 

middleware.SignMiddleware = SignMiddleware

