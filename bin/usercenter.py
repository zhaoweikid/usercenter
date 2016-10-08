# coding: utf-8
import os, sys
import json, random, hashlib
from zbase.base.logger import log
from zbase.web import core 
import pdb

#pdb.set_trace()

ERR  = -1

class Index (RequestHandler):
    def get(self):
        self.write('haha, good!')

class UserBase (RequestHandler):
    table  = 'users'
    dbname = 'usercenter'
    login_validator    = [Field(name='password',match=TypeAscStr), 
                          Field(name='email',match=TypeEmail)]
    register_validator = [Field(name='password',match=TypeAscStr), 
                          Field(name='email',match=TypeEmail)]
    
    def get(self, name):
        try:
            func = getattr(self, name)
            return func()
        except:
            log.info(traceback.format_exc())
            return self.failed()

    def post(self, name):
        return self.get(name)

    def succ(self, ses=None):
        if ses:
            obj = {'ret':0, 'uid':ses['uid']}
            s = json.dumps(obj)
            log.info('succ: %s', s)
            self.write(s)
            return
            #return {'ret':0, 'uid':ses['uid']}
        log.info('succ')
        self.write('{"ret":0}')

    def failed(self, errstr=u'内部错误'):
        log.info("failed: %s", errstr)
        obj = {'ret':ERR, 'error':errstr}
        s = json.dumps(obj)
        log.info('failed: %s', s)
        self.write(s)


    def create_password(self, passwd, salt=None):
        if salt is None:
            salt = random.randint(1, 1000000)
        saltstr = '%06d' % salt 
        return 'sha1$%s$%s' % (salt, hashlib.sha1(passwd+saltstr).hexdigest())

    def login(self):
        data = web.input(self.request, self.login_validator)
    
        conn = dbpool.acquire(self.dbname)
        try:
            username = data.get('username', InputNone)
            password = data.get('password', InputNone)
            email    = data.get('email', InputNone)
            log.info("username:%s email:%s password:%s" % (username.v, email.v, password.v))
 
            if not password.v:
                return self.failed('password must not null')

            if email.v:
                self.login_key = 'email'
            elif username.v:
                self.login_key = 'username'
            else:
                return self.failed('username or email must not null')

            keydata  = data.get(self.login_key, InputNone).v
            if not keydata:
                return self.failed(self.login_key + ' must not null')

            ret = conn.get("select id,username,email,password from %s where %s='%s'" % \
                            (self.table, self.login_key, conn.escape(keydata)), isdict=False)
            if not ret:
                return self.failed(self.login_key + ' not found')

            px = ret[3].split('$')
            pass_enc = self.create_password(password.v, px[1])
            if ret[3] != pass_enc:
                return self.failed('password error')
                    
            ses = session.Session()
            ses.start()
            ses['uid']      = ret[0]
            ses['username'] = ret[1]
            ses['email']    = ret[2]
            ses.end(self.request)

            resp = self.succ(ses)
            return resp
        except Exception, e:
            log.error(traceback.format_exc())
            return self.failed('Exception:' + str(e))
        finally:
            dbpool.release(conn)


    @session.check_login
    def logout(self):
        self.ses.clear() 
        return self.succ()

    def register(self):
        log.info('register')
        data = web.input(self.request, self.register_validator)
        log.info('data:%s', data)
        
        email = data.getv('email','')
        pass_enc = self.create_password(data.getv('password'))
        data.get('password').setval([pass_enc])
        keys = ['email','password']
        keystr = ','.join(keys)
        #log.info([ x for x in data.iterkeys()])
        #valstr = ','.join([dbmodel.Value(x.v) for x in data.iterkeys() if x in keys])  

        conn = dbpool.acquire(self.dbname)
        try:
            sql = "select id from %s where email='%s'" % (self.table, email)
            log.info(sql)
            ret = conn.query(sql)
            if len(ret) >= 1:
                return self.failed('username or email exist')

            email_esc = conn.escape(email)
            #sql = "insert into %s(%s) values (%s)" % (self.table, keystr, valstr)
            sql = "insert into %s(email,password,username) values ('%s','%s','%s')" % \
                (self.table, email_esc, conn.escape(pass_enc), email_esc)
            log.info(sql)
            conn.execute(sql)
            lastid = conn.last_insert_id()
            
            ses = session.session_start()
            ses['uid'] = lastid
            ses['username'] = data.getv('username', '')
            ses['email']    = email
            ses.end(self)

            resp = self.succ(ses)
            return resp
        except Exception, e:
            log.error(traceback.format_exc())
            return self.failed('error:' + str(e))
        finally:
            dbpool.release(conn)



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


class GroupBase (RequestHandler):
    pass




