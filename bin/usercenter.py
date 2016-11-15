# coding: utf-8
import os, sys
import json, random, hashlib
from zbase.web import core 
import logging
from userbase import BaseHandler
#import pdb
#pdb.set_trace()

log = logging.getLogger()

class Ping (core.Handler):
    def GET(self):
        self.write('pong')


class UserBase (BaseHandler):
    table  = 'users'
    dbname = 'usercenter'
    
    @with_validator([Field(name='password',match=TypeAscStr), 
                     Field(name='username',match=TypeStr),
            ])
    def login(self):
        data = self.validtor.data
    
        try:
            username = data.get('username')
            password = data.get('password')
            log.info("username:%s password:%s" % (username, password))
 
            if not password:
                return self.fail('password must not null')

            login_key = 'username'
            if re.match(TYPE_MAP[T_MAIL]):
                login_key = 'email'
            elif re.match(TYPE_MAP[T_MOBILE]):
                login_key = 'mobile' 

            with get_connection(self.dbname) as conn:
                where = {
                    login_key: username
                }
                ret = conn.select_one(self.table, where, "id,username,email,password")
                if not ret:
                    return self.fail(login_key + ' not found')

            px = ret['password'].split('$')
            pass_enc = userbase.create_password(password, px[1])
            if ret['password'] != pass_enc:
                return self.fail('password error')
                    
            self.create_session()
            self.ses['uid']      = ret['id']
            self.ses['username'] = ret['username']
            self.ses['email']    = ret['email']

            resp = self.succ({'uid':ret['id']})
            return resp
        except Exception, e:
            log.error(traceback.format_exc())
            return self.fail('Exception:' + str(e))


    @session.check_login
    def logout(self):
        self.ses.delete() 
        return self.succ()


    @with_validator([Field(name='password',match=T_STR), 
                     Field(name='username',match=T_STR),
                     Field(name='email',match=T_EMAIL),
                     Field(name='mobile',match=T_MOBILE),
            ])
    def register(self):
        log.info('register')
        data = self.validtor.data
        log.info('data:%s', data)
        
        email = data.get('email','')
        mobile = data.get('mobile','')
        username = data.get('username','')
        password = data.get('password','')
        pass_enc = userbase.create_password(password)

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
                'password': password,
            }

            with get_connection(self.dbname) as conn:
                ret = conn.select(self.table, where, 'id')
                if len(ret) >= 1:
                    return self.failed('username or email or mobile exist')
                conn.insert(self.table, insertdata)
            lastid = conn.last_insert_id()
            
            ses = session.create_session()
            ses['uid'] = lastid
            ses['username'] = data.getv('username', '')
            ses['email']    = email

            resp = self.succ(ses)
            return resp
        except Exception, e:
            log.error(traceback.format_exc())
            return self.failed('error:' + str(e))


class UserLogin (UserBase):
    def get(self):
        try:
            self.login()
        except Exception, e:
            self.failed()


class UserLogout (UserBase):
    def get(self):
        try:
            self.logout()
        except Exception, e:
            self.failed()


class UserRegister (UserBase):
    def get(self):
        try:
            self.register()
        except Exception, e:
            log.error(traceback.format_exc())
            self.failed()

class UserInfo (UserBase):
    def GET(self):
        valid = [Field(name='id',match=TypeInt), Field(name='email',match=TypeStr)]
        data  = web.input(self.request, valid)
        email = data.getv('email', None)
        uid   = data.getv('id')
        if not uid and not email:
            return failed('user id/email error')
        try:
            ret = Users.db().select().where(data).query()
            return self.succ(ret)
        except Exception, e:
            return self.failed()

    def succ(self, data):
        return {'ret':0, 'data':data}
 
class UserModify (UserBase):
    def GET(self):
        valid = [Field(name='id',match=TypeInt), 
                 Field(name='mobile',match=TypeStr,isnull=True),
                 Field(name='email',match=TypeStr,isnull=True),
                 Field(name='password',match=TypeAscStr,isnull=True),
                 Field(name='status',match=TypeInt,isnull=True),
                 Field(name='extend',match=TypeStr,isnull=True),
                ]
        data = web.input(self.request, valid)
        uid = data.getv('id')
        if not uid:
            return failed('user id error')
        if len(data) == 1:
            return failed('argument error')
        try:
            del data['id']
            Users.db().update(data).where(id=userid).execute()
            return self.succ()
        except Exception, e: 
            return self.failed()
        

class UserList (UserBase):
    pass

class UserLog (UserBase):
    pass




