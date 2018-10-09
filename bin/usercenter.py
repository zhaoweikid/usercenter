# coding: utf-8
import os, sys
import json, random, hashlib
import time
from zbase3.web import core
from zbase3.web.validator import *
from zbase3.base.dbpool import get_connection
from zbase3.utils import createid
import logging
from userbase import *

#import pdb
#pdb.set_trace()

log = logging.getLogger()

class Ping (core.Handler):
    def GET(self):
        self.write('pong')


class UserBase (BaseHandler):
    table  = 'users'
    dbname = 'usercenter'
    
    @with_validator([F('username'), F('password', must=True), F('email', T_MAIL), F('mobile', T_MOBILE)])
    def login(self):
        data = self.validator.data
    
        try:
            username = data.get('username')
            password = data.get('password')
            email    = data.get('email')
            mobile   = data.get('mobile')

            if not username and not email and not mobile:
                return self.fail(ERR, 'username/email/mobile must have one')

            if username:
                login_key = 'username'
            elif mobile:
                login_key = 'mobile'
            elif email:
                login_key = 'email'

            ret = None
            with get_connection(self.dbname) as conn:
                where = {
                    login_key: data.get(login_key)
                }
                #log.debug('where:%s', where)
                ret = conn.select_one(self.table, where, "id,username,email,password,isadmin")
                log.debug('select:%s', ret)
                if not ret:
                    return self.fail(ERR_USER, login_key + ' not found')
                conn.update(self.table, where, {'logtime':int(time.time())})
            if not ret:
                return self.fail(ERR_USER, 'db error')

            # password:   sha1$123456$AJDKLJDLAKJKDLSJKLDJALASASASA
            px = ret['password'].split('$')
            pass_enc = create_password(password, int(px[1]))
            if ret['password'] != pass_enc:
                return self.fail(ERR_AUTH, 'password error')
          
            self.create_session()
            sesdata = {'userid':ret['id'], 'username':ret['username'], 'isadmin':ret['isadmin']}
            self.ses.update(sesdata)

            self.succ({'userid':ret['id']})
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'Exception:' + str(e))



    @with_validator([F('username'), 
                     F('password', must=True), 
                     F('email', T_MAIL),
                     F('mobile', T_MOBILE),
            ])
    def register(self):
        data = self.validator.data
        log.info('data:%s', data)
        
        email = data.get('email','')
        mobile = data.get('mobile','')
        username = data.get('username','')
        password = data.get('password','')
        pass_enc = create_password(password)

        try:
            where = {}
            insertdata = {
                'password': pass_enc,
                'ctime': int(time.time()),
            }
            if email:
                where['email'] = email
                insertdata['email'] = email
            if mobile:
                where['mobile'] = mobile
                insertdata['mobile'] = mobile
            if username:
                where['username'] = username
                insertdata['username'] = username

            if not email and not mobile:
                return self.fail(ERR_PARAM, 'email/mobile must not null')

            lastid = -1
            with get_connection(self.dbname) as conn:
                ret = conn.select(self.table, where, 'id')
                if len(ret) >= 1:
                    return self.fail(ERR_USER, 'username or email or mobile exist')
                insertdata['id'] = createid.new_id64(conn=conn)
                conn.insert(self.table, insertdata)
            
            self.create_session()
            sesdata = {'userid':insertdata['id'], 'username':username, 'isadmin':0}
            self.ses.update(sesdata)

            resp = self.succ({'userid':str(insertdata['id']), 'username':username, 'email':email, 'mobile':mobile})
            return resp
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'error:' + str(e))

    def get_user(self):
        userid = self.ses['userid']
        where = {'id':userid}
        user = None
        with get_connection(self.dbname) as conn:
            user = conn.select_one(self.table, where)
            if not user:
                return self.fail(ERR_USER, 'not have user info')
        for k in ['password', 'regip', 'isadmin']:
            user.pop(k)

        user['id'] = str(user['id'])

        if user['extend']:
            user['extend'] = json.loads(user['extend'])

        return self.succ(user)

    def get_user_list(self):
        if not self.ses.get('isadmin', 0):
            return self.fail(ERR_PERM, 'permission deny')
            
        data = self.input()
        pagecur  = int(data.get('pagecur', 1))
        pagesize = int(data.get('pagesize', 20))

        page = None
        with get_connection(self.dbname) as conn:
            sql = conn.select_sql(self.table)
            page = conn.select_page(sql, pagecur=pagecur, pagesize=pagesize)

        pdata = page.pagedata.data
        for row in pdata:
            for k in ['password']:
                row.pop(k)
            row['id'] = str(row['id'])
            if row['extend']:
                row['extend'] = json.loads(row['extend'])

        pagedata = {
            'cur':page.page, 
            'size':page.page_size, 
            'count':page.count, 
            'pages':page.pages, 
            'data':pdata,
        }
        return self.succ(pagedata)

    @with_validator([F('username'), 
                     F('password'), 
                     F('extend'),
                     F('id', T_INT),
    ]) 
    def modify_user(self, userid):
        # modify username/status/password/extend
        userid = int(userid)
        isadmin = self.ses['isadmin']
        suid = self.ses['userid']

        if not isadmin and userid != suid:
            return self.fail(ERR_PERM)

        data = self.validator.data
        values = {}
        where  = {'id':userid}
       
        for k in ['username', 'password', 'extend']:
            if k == 'password' and data.get('password'):
                values['password'] = create_password(data['password'])
            elif k == 'extend' and data.get('extend'):
                x = json.loads(data.get('extend'))
                values['extend'] = data['extend']
            elif data[k]:
                values[k] = data[k]

        values['uptime'] = int(time.time())

        with get_connection(self.dbname) as conn:
            ret = conn.update(self.table, values, where)
            if ret != 1:
                return self.fail(ERR, 'condition error')

        values['id'] = str(where['id'])
        return self.succ(values)

class User (UserBase):
    noses_path = {
        '/v1/user':'POST', 
        '/v1/user/login':'GET',
    }

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

    def PUT(self, userid):
        # update
        return self.modify_user(userid)

    def error(self, data):
        self.fail(ERR_PARAM)

    def input(self):
        data = self.req.input()
        if data:
            return data
        return self.req.inputjson()








