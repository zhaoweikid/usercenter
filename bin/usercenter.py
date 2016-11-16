# coding: utf-8
import os, sys
import json, random, hashlib
from zbase.web import core
from zbase.web.validator2 import *
from zbase.base.dbpool import get_connection
from zbase.utils import createid
import logging
from userbase import BaseHandler, check_login, create_password
#import pdb
#pdb.set_trace()

log = logging.getLogger()

class Ping (core.Handler):
    def GET(self):
        self.write('pong')


class UserBase (BaseHandler):
    table  = 'users'
    dbname = 'usercenter'
    
    @with_validator(['username', 'password'])
    def login(self):
        data = self.validator.data
    
        try:
            username = data.get('username')
            password = data.get('password')
            log.info("username:%s password:%s" % (username, password))
 
            if not password:
                return self.fail('password must not null')

            login_key = 'email'
            if TYPE_MAP[T_MAIL].match(username):
                login_key = 'email'
            elif TYPE_MAP[T_MOBILE].match(username):
                login_key = 'mobile'
            else:
                return self.fail('login key error, must email/mobile')

            with get_connection(self.dbname) as conn:
                where = {
                    login_key: username
                }
                ret = conn.select_one(self.table, where, "id,username,email,password,isadmin")
                if not ret:
                    return self.fail(login_key + ' not found')

            px = ret['password'].split('$')
            pass_enc = create_password(password, int(px[1]))
            if ret['password'] != pass_enc:
                return self.fail('password error')
           
            sesdata = {'uid':ret['id'], 'username':ret['username'], 'isadmin':ret['isadmin']}
            self.create_user_session(sesdata)
            resp = self.succ({'uid':ret['id']})
            return resp
        except Exception, e:
            log.error(traceback.format_exc())
            return self.fail('Exception:' + str(e))



    @with_validator(['username', 'password', 
                     F('email', T_MAIL),
                     F('mobile', T_MOBILE),
            ])
    def register(self):
        log.info('register')
        data = self.validator.data
        log.info('data:%s', data)
        
        email = data.get('email','')
        mobile = data.get('mobile','')
        username = data.get('username','')
        password = data.get('password','')
        pass_enc = create_password(password)

        try:
            where = {}
            if email:
                where['email'] = email
            if mobile:
                where['mobile'] = mobile
            if username:
                where['username'] = username

            insertdata = {
                'username': username,
                'email': email,
                'mobile': mobile,
                'password': pass_enc,
            }


            lastid = -1
            with get_connection(self.dbname) as conn:
                ret = conn.select(self.table, where, 'id')
                if len(ret) >= 1:
                    return self.fail('username or email or mobile exist')
                insertdata['id'] = createid.new_id64(conn=conn)
                conn.insert(self.table, insertdata)
            
            self.create_user_session({'uid':insertdata['id'], 'username':username, 'isadmin':0})
            resp = self.succ({'uid':insertdata['id']})
            return resp
        except Exception, e:
            log.error(traceback.format_exc())
            return self.fail('error:' + str(e))

    def create_user_session(self, data):
        self.create_session()
        self.ses.update(data)
    
    @check_login
    def get_user(self):
        uid = self.ses['uid']
        where = {'id':uid}
        user = None
        with get_connection(self.dbname) as conn:
            user = conn.select_one(self.table, where)
            if not user:
                return self.fail('not have user info')
        for k in ['password', 'regip', 'isadmin']:
            user.pop(k)
        if user['extend']:
            user['extend'] = json.loads(user['extend'])

        return self.succ(user)

    @check_login
    def get_user_list(self):
        if not self.ses.get('isadmin', 0):
            return self.fail('permission deny')

        page = None
        with get_connection(self.dbname) as conn:
            page = conn.select_page(self.table, sql, pagecur=pagecur, pagesize=pagesize)

        pagedata = {
            'cur':page.page, 
            'size':page.pagesize, 
            'count':page.count, 
            'data':page.pagedata,
        }
        return self.succ(pagedata)

    @check_login
    @with_validator(['username', 'password', 'extend',
                     F('id', T_INT),
                     F('status', T_INT),
    ]) 
    def modify_user(self):
        # modify username/status/password/extend
        data = self.validator.data
        values = {}
        where  = {}
        if self.ses['isadmin']:
            where['id'] = data['id']
        else:
            where['id'] = self.ses['uid']
       
        for k in ['username', 'status', 'password', 'extend']:
            if k == 'password' and data.get('password'):
                values['password'] = create_password(data['password'])
            elif k == 'extend' and data.get('extend'):
                x = json.loads(data.get('extend'))
                values['extend'] = data['extend']
            else:
                values[k] = data[k]

        values['uptime'] = int(time.time())

        with get_connection(self.dbname) as conn:
            conn.update(self.table, values, where)

        values['id'] = where['id']
        return self.succ(values)

class User (UserBase):
    def GET(self, name=None):
        # select
        if name == 'login':  # /login
            return self.login()
        elif name == 'logout': # /logout
            if self.ses:
                self.ses.remove()
            return self.succ()
        elif name: # /id
            return self.get_user()
        else: # list
            return self.get_user_list()

    def POST(self):
        # create
        return self.register()

    def PUT(self):
        # update
        return self.modify_user()

