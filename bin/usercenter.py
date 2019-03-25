# coding: utf-8
import os, sys
import json, random, hashlib
import time
import copy
from zbase3.web import core, cache
from zbase3.web.validator import *
from zbase3.base.dbpool import get_connection
from zbase3.utils import createid
import logging
from userbase import *

#import pdb
#pdb.set_trace()

log = logging.getLogger()

class Ping (BaseHandler):
    def GET(self):
        data = {'time':int(time.time()), 'content':'pong'}
        self.succ(data)


class UserBase (BaseHandler):
    table  = 'users'
    dbname = 'usercenter'


    @cache.with_cache(60)
    def login_settings(self):
        retdata = {}
        with get_connection(self.dbname) as conn:
            ret = conn.select('settings')
            if not ret:
                retdata = {}
            else:
                for row in ret:
                    retdata[row['name']] = row['value']

        return retdata
    
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

            self.succ({'userid':str(ret['id']), 'username':ret['username']})
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
            sesdata = {'userid':int(insertdata['id']), 'username':username, 'isadmin':0}
            self.ses.update(sesdata)

            resp = self.succ({'userid':str(insertdata['id']), 'username':username, 'email':email, 'mobile':mobile})
            return resp
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'error:' + str(e))

    def get_user(self):
        userid = int(self.ses['userid'])
        where = {'id':userid}
        user = None
        groups = None
        fields ='id,username,password,email,mobile,head,score,stage,FROM_UNIXTIME(ctime) as ctime,FROM_UNIXTIME(utime) as utime,logtime,regip,status,isadmin,extend'
        with get_connection(self.dbname) as conn:
            user = conn.select_one(self.table, where, fields=fields)
            if not user:
                return self.fail(ERR_USER, 'not have user info')

            groups = conn.query('select g.id as id,g.name as name from user_group ug, groups g where g.id=ug.groupid and ug.userid=%d' % userid)
            user['group'] = groups     

            user['role'] = []
            user['perm'] = []
            user['allperm'] = []

            userperm = conn.query('select permid,roleid from user_perm where userid=%d' % userid)
            if userperm:
                roles = [ x['roleid'] for x in userperm if x['roleid']>0 ]
                perms = [ x['permid'] for x in userperm if x['permid']>0 ]
        
                if roles:
                    ret = conn.select('roles', where={'id':('in', roles)}, fields='id,name')
                    if ret:
                        user['role'] = ret

                if perms:
                    ret = conn.select('perms', where={'id':('in', perms)}, fields='id,name')
                    if ret:
                        user['perm'] = ret
                        user['allperm'] = ret

                if roles:
                    ret = conn.query('select p.id as id,p.name as name from perms p, role_perm rp where rp.roleid in (%s) and rp.permid=p.id' % \
                        (conn.exp2sql('rp.roleid', 'in', roles)))
                    if ret:
                        xids = [x['id'] for x in user['allperm']]
                        for row in ret:
                            if row['id'] not in xids:
                                user['allperm'].append(row)


            allperm = [ x['name'] for x in user['allperm'] ]
            self.ses['allperm'] = allperm

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
            'page':page.page, 
            'pagesize':page.page_size, 
            'pagenum':page.pages, 
            'data':pdata,
        }
        return self.succ(pagedata)

    @with_validator([F('username'), 
                     F('password'), 
                     F('status', T_INT), 
                     F('extend'),
                     F('id', T_INT),
    ]) 
    def modify_user(self):
        # modify username/status/password/extend
        #isadmin = self.ses['isadmin']
        userid = self.ses['userid']

        data = self.validator.data
        values = {}
        where  = {'id':userid}
       
        for k in ['username', 'password', 'extend']:
            v = data.get(k)
            if k == 'password' and v:
                values['password'] = create_password(v)
            elif k == 'extend' and v:
                x = json.loads(v)
                values['extend'] = v
            elif v:
                values[k] = v

        log.debug('update values:%s', values)
        if not values:
            log.info('no modify info')
            return self.fail(ERR_PARAM)

        values['utime'] = int(time.time())

        with get_connection(self.dbname) as conn:
            ret = conn.update(self.table, values, where)
            if ret != 1:
                return self.fail(ERR, 'condition error')

        values['id'] = str(where['id'])
        return self.succ(values)

    @with_validator([F('groupid', T_INT)])
    def add_group(self):
        data = self.validator.data
        groupid = data.get('groupid')
       
        t = int(time.time())
        with get_connection(self.dbname) as conn:
            data = {
                'id': createid.new_id64(conn=conn),
                'userid':self.ses['userid'],
                'groupid':groupid,
                'ctime':t,
                'utime':t,
            }
            ret = conn.insert('user_group', data)
            if ret != 1:
                return self.fail(ERR_DB)

            ret = conn.select_one('user_group', where={'id':data['id']})
            return succ(ret)


    @with_validator([F('groupid', T_INT)])
    def del_group(self):
        data = self.validator.data
        groupid = data.get('groupid')
        userid = self.ses['userid']

        with get_connection(self.dbname) as conn:
            ret = conn.delete('user_group', where={'userid':userid, 'groupid':groupid})
            return self.succ(ret)

    @with_validator([F('permid', T_INT, default=0), F('roleid', T_INT, default=0)])
    def add_perm_role(self):
        data = self.validator.data
        roleid = data.get('roleid')
        permid = data.get('permid')
       
        t = int(time.time())
        with get_connection(self.dbname) as conn:
            data = {
                'id': createid.new_id64(conn=conn),
                'userid':self.ses['userid'],
                'roleid':0,
                'permid':0,
                'ctime':t,
                'utime':t,
            }
            if roleid:
                data['roleid'] = roleid
            else:
                data['permid'] = permid
                
            ret = conn.insert('user_perm', data)
            if ret != 1:
                return self.fail(ERR_DB)

            ret = conn.select_one('user_perm', where={'id':data['id']})
            return self.succ(ret)


    @with_validator([F('permid', T_INT, default=0), F('roleid', T_INT, default=0)])
    def del_perm_role(self):
        data = self.validator.data
        roleid = data.get('roleid')
        permid = data.get('permid')

        with get_connection(self.dbname) as conn:
            if roleid:
                ret = conn.delete('user_perm', where={'userid':userid, 'roleid':('in', roleids)})
            if permid:
                ret = conn.delete('user_perm', where={'userid':userid, 'permid':('in', permids)})

            return self.succ()



class User (UserBase):
    noses_path = {
        '/v1/user/signup':'POST', 
        '/v1/user/login':'GET',
    }

    def GET(self, name=None):
        log.warn('====== GET %s %s ======', self.req.path, self.req.query_string)
        try:
            if name == 'login':  # /login
                return self.login()
            elif name == 'logout': # /logout
                if self.ses:
                    self.ses.remove()
                return self.succ()
            elif name == 'q':
                return self.get_user()
            elif name == 'list':
                return self.get_user_list()
        except:
            log.error(traceback.format_exc())
            self.fail(ERR_PARAM)

    def POST(self, name):
        log.warn('====== POST %s %s ======', self.req.path, self.req.query_string)
        try:
            if name == 'signup':
                return self.register()
            elif name == 'mod':
                return self.modify_user()
            elif name == 'addgroup':
                return self.add_group()
            elif name == 'delgroup':
                return self.del_group()
            elif name == 'addperm':
                return self.add_perm_role()
            elif name == 'delperm':
                return self.del_perm_role()

        except:
            log.error(traceback.format_exc())
            self.fail(ERR_PARAM)


    def error(self, data):
        self.fail(ERR_PARAM)

    def input(self):
        data = self.req.input()
        if data:
            return data
        return self.req.inputjson()


 

      
