# coding: utf-8
import os, sys
import json, random, hashlib
import time
import copy
from zbase3.web import core, cache, httpcore
from zbase3.web.validator import *
from zbase3.base.dbpool import get_connection, DBFunc
from zbase3.utils import createid
import logging
from userbase import *
import utils


log = logging.getLogger()

class Ping (BaseHandler):
    session_nocheck = [
        '/uc/v1/ping',
    ]

    def GET(self):
        data = {'time':int(time.time()), 'content':'pong'}
        self.succ(data)


class UserBase (BaseHandler):
    table  = 'users'
    dbname = 'usercenter'

    @cache.with_cache(60)
    def settings(self):
        retdata = {}
        with get_connection(self.dbname) as conn:
            ret = conn.select('settings')
            if not ret:
                retdata = {}
            else:
                for row in ret:
                    retdata[row['name']] = row['value']

        return retdata
    
    @with_validator([
        F('username'), 
        F('password', must=True), 
        F('email', T_MAIL), 
        F('mobile', T_MOBILE),
    ])
    def signin(self):
        try:
            username = self.data.get('username')
            password = self.data.get('password')
            email    = self.data.get('email')
            mobile   = self.data.get('mobile')

            if not username and not email and not mobile:
                return ERR, 'username/email/mobile must have one'

            if username:
                login_key = 'username'
            elif mobile:
                login_key = 'mobile'
            elif email:
                login_key = 'email'

            ret = None
            with get_connection(self.dbname) as conn:
                where = {
                    login_key: self.data.get(login_key)
                }
                #log.debug('where:%s', where)
                ret = conn.select_one(self.table, where, "id,username,email,password,isadmin,status")
                log.debug('select:%s', ret)
                if not ret:
                    return ERR_USER, login_key + ' not found'

                # password:   sha1$123456$AJDKLJDLAKJKDLSJKLDJALASASASA
                px = ret['password'].split('$')
                pass_enc = create_password(password, int(px[1]))
                if ret['password'] != pass_enc:
                    return ERR_AUTH, 'username or password error'

                if ret['status'] != STATUS_OK:
                    return ERR_AUTH, "status error"
     
                conn.update(self.table, {'logtime':int(time.time())}, where={'id':ret['id']})

                retcode, userinfo = self.get_user(ret['id'])
                log.debug('get user: %d %s', retcode, userinfo)

            sesdata = {
                'userid':int(ret['id']), 
                'username':ret['username'], 
                'isadmin':ret['isadmin'], 
                'status': userinfo['status'],
                'allperm':[ x['name'] for x in userinfo['allperm']],
            }
            self.ses.update(sesdata)
            
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'Exception:' + str(e))

    @with_validator([
        F('appid', must=True), 
        F('code', must=True),
        F('openid'), 
    ])
    def signin_3rd(self):
        try:
            appid = self.data.get('appid')
            code  = self.data.get('code')
            openid = self.data.get('openid')

            if not openid:
                openid = utils.get_openid(code, appid)
                if not openid:
                    return ERR_AUTH, 'openid error'

            ret = None
            with get_connection(self.dbname) as conn:
                where = {
                    'appid': appid,
                    'openid': openid,
                }
                ret = conn.select_one('openuser', where, 'userid')
                if not ret:
                    return ERR_AUTH, 'apppid/openid error'

                userid = ret['userid']

                #log.debug('where:%s', where)
                ret = conn.select_one(self.table, {'id':userid}, "id,username,email,password,isadmin,status")
                log.debug('select:%s', ret)
                if not ret:
                    return ERR_USER, ' appid/openid not found'

                conn.update(self.table, {'logtime':int(time.time())}, where={'id':userid})

            retcode, userinfo = self.get_user(ret['id'])
            sesdata = {
                'userid':int(ret['id']), 
                'username':ret['username'], 
                'isadmin':ret['isadmin'], 
                'status': userinfo['status'],
                'allperm':[ x['name'] for x in userinfo['allperm']],
                'appid':appid,
                'openid':openid,
                'plat':config.OPENUSER_ACCOUNT[appid]['plat'],
            }
            self.ses.update(sesdata)

            #self.succ({'id':str(ret['id']), 'username':ret['username']})
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'Exception:' + str(e))


    @with_validator([
        F('username'), 
        F('password', must=True), 
        F('email', T_MAIL),
        F('mobile', T_MOBILE),
    ])
    def signup(self):
        log.info('data:%s', self.data)
        
        email    = self.data.get('email','')
        mobile   = self.data.get('mobile','')
        username = self.data.get('username','')
        password = self.data.get('password','')
        pass_enc = create_password(password)

        try:
            where = {}
            insertdata = {
                'password': pass_enc,
                'ctime': int(time.time()),
                'status': STATUS_OK,  # 默认状态为2
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
                return ERR_PARAM, 'email/mobile must not null'

            lastid = -1
            with get_connection(self.dbname) as conn:
                ret = conn.select(self.table, where, 'id')
                if len(ret) >= 1:
                    return ERR_USER, 'username or email or mobile exist'
                insertdata['id'] = createid.new_id64(conn=conn)
                conn.insert(self.table, insertdata)
          
            # 没有session才能创建新session
            if not self.ses:
                self.create_session()
                log.debug('create sesssion:%s', self.ses.sid)
                sesdata = {
                    'userid':int(insertdata['id']), 
                    'username':username, 
                    'isadmin':0, 
                    'status':insertdata['status'],
                }
                self.ses.update(sesdata)

            retcode, userinfo = self.get_user(insertdata['id'])
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'error:' + str(e))

    @with_validator([
        F('appid', must=True), 
        F('code', must=True), 
        F('id', T_INT), 
        F('openid'), 
    ])
    def signup_3rd_args(self):
        appid = self.data.get('appid')
        code  = self.data.get('code')
        userid= self.data.get('id')
        openid= self.data.get('openid')

        if not openid:
            openid = utils.get_openid(code, appid)
            if not openid:
                return ERR_AUTH, 'openid error'
            
        return self.signup_3rd(appid, openid, userid)

    def signup_3rd(self, appid, openid, userid=None):
        try:
            where = {
                'appid':appid,
                'openid':openid,
            }
            user_data = {
                'password': '',
                'ctime': int(time.time()),
                'status': STATUS_OK,  # 默认状态为2
            }

            lastid = -1
            with get_connection(self.dbname) as conn:
                ret = conn.select_one('openuser', where=where, fields='userid')
                if ret:
                    return ERR_USER, 'user exist'

                if userid:
                    ret = conn.select_one(self.table, where={'id':userid}, fields='id')
                    if not ret:
                        return ERR_USER, 'user error'

                
                if not userid:
                    user_data['id'] = createid.new_id64(conn=conn)
                    user_data['username'] = 'user_%d' % (user_data['id'])
                    conn.insert(self.table, user_data)

                openuser_data = {
                    'id': createid.new_id64(conn=conn),
                    'userid':user_data['id'],
                    'appid':appid,
                    'openid':openid,
                    'plat':config.OPENUSER_ACCOUNT[appid]['plat'],
                    'ctime':DBFunc('UNIX_TIMESTAMP(now())'),
                }
                conn.insert('openuser', openuser_data)
          
            # 没有session才能创建新session
            if not self.ses:
                self.create_session()
                log.debug('create sesssion:%s', self.ses.sid)
                sesdata = {
                    'userid':int(user_data['id']), 
                    'username':'', 
                    'isadmin':0, 
                    'status':user_data['status'],
                    'appid':appid,
                    'openid':openid,
                    'plat':config.OPENUSER_ACCOUNT[appid]['plat'],
                }
                self.ses.update(sesdata)

            retcode, userinfo = self.get_user(user_data['id'])
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'error:' + str(e))


    @with_validator([
        F('appid', must=True), 
        F('code', must=True),
        F('openid'), 
    ])
    def signauto_3rd(self):
        try:
            appid = self.data.get('appid')
            code  = self.data.get('code')
            openid = self.data.get('openid')

            if not openid:
                openid = utils.get_openid(code, appid)
                if not openid:
                    return ERR_AUTH, 'openid error'

            ret = None
            with get_connection(self.dbname) as conn:
                where = {
                    'appid': appid,
                    'openid': openid,
                }
                ret = conn.select_one('openuser', where, 'userid')
                if not ret: # not found user
                    return self.signup_3rd(appid, openid)

                userid = ret['userid']

                #log.debug('where:%s', where)
                ret = conn.select_one(self.table, {'id':userid}, "id,username,email,password,isadmin,status")
                log.debug('select:%s', ret)
                if not ret:
                    return ERR_USER, ' appid/openid not found'

                conn.update(self.table, {'logtime':int(time.time())}, where={'id':userid})
        
            retcode, userinfo = self.get_user(ret['id'])
            sesdata = {
                'userid':int(ret['id']), 
                'username':ret['username'], 
                'isadmin':ret['isadmin'], 
                'status': userinfo['status'],
                'allperm':[ x['name'] for x in userinfo['allperm']],
                'appid':appid,
                'openid':openid,
                'plat':config.OPENUSER_ACCOUNT[appid]['plat'],
            }
            self.ses.update(sesdata)
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            return self.fail(ERR, 'Exception:' + str(e))


    @with_validator([F('id', T_INT),])
    def get_user_info(self):
        userid_in = self.data.get('id', 0)
        userid  = self.ses.get('userid', 0)
        isadmin = self.ses.get('isadmin', 0)
        
        if userid_in and  userid != userid_in:
            if not isadmin:
                log.info('userid_in:%d userid:%d isadmin:%d', userid_in, userid, isadmin)
                return ERR_PERM, 'permission deny'
            else:
                userid = userid_in

        retcode, data = self.get_user(userid)
        return retcode, data

    def get_user(self, userid):
        userid = int(userid)

        where = {'id':userid}
        user = None
        groups = None
        fields ='id,username,password,email,mobile,head,score,stage,FROM_UNIXTIME(ctime) as ctime,' \
            'FROM_UNIXTIME(utime) as utime,FROM_UNIXTIME(logtime) as logtime,regip,status,isadmin,extend'
        with get_connection(self.dbname) as conn:
            user = conn.select_one(self.table, where, fields=fields)
            if not user:
                return ERR_USER, 'not have user info'

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


            #allperm = [ x['name'] for x in user['allperm'] ]
            #self.ses['allperm'] = allperm

        for k in ['password', 'regip', 'isadmin']:
            user.pop(k)

        user['id'] = str(user['id'])
        
        if user['extend']:
            user['extend'] = json.loads(user['extend'])

        return OK, user

    @with_validator([
        F('page',T_INT,default=1), 
        F('pagesize',T_INT,default=20),
        F('username'),
        F('mobile', T_MOBILE),
        F('ctime', T_DATETIME),
    ])
    def get_user_list(self):
        if not self.ses.get('isadmin', 0):
            return ERR_PERM, 'permission deny'
            
        data = self.data
        pagecur  = int(data.get('page', 1))
        pagesize = int(data.get('pagesize', 20))

        page = None

        log.debug('data:%s', data)
        where = {}
        username = data.get('username')
        if username:
            where['username'] = username

        mobile = data.get('mobile')
        if mobile:
            where['mobile'] = mobile

        ctime = data.get('ctime')
        if ctime:
            where['ctime'] = (
                'between', 
                (DBFunc('UNIX_TIMESTAMP("%s")' % ctime[0]), 
                 DBFunc('UNIX_TIMESTAMP("%s")' % ctime[1]))
            )

        groups = {}
        roles = {}
        perms = {}
        with get_connection(self.dbname) as conn:
            sql = conn.select_sql(self.table, where=where)
            page = conn.select_page(sql, pagecur=pagecur, pagesize=pagesize)
               
            # 获取组
            useridstr = ','.join([ str(x['id']) for x in page.pagedata.data])
            sql = "select ug.userid as userid, ug.groupid as groupid, g.name as name,g.info as info from user_group as ug, groups as g " \
                  "where ug.userid in(%s) and ug.groupid=g.id" % (useridstr)

            ret = conn.query(sql)
            log.debug('groups:%s', ret)

            for row in ret:
                uid = row['userid']
                items = groups.get(uid)
                if not items:
                    items = []
                    groups[uid] = items
                items.append({'id':str(row['groupid']), 'name':row['name'], 'info':row['info']})

            # 获取权限
            sql = "select up.userid as userid, up.permid as permid, p.name as name, p.info as info from user_perm as up,perms as p " \
                  "where up.userid in (%s) and up.permid=p.id" % (useridstr)
            ret = conn.query(sql)
            log.debug('perms:%s', ret)
            
            for row in ret:
                uid = row['userid']
                items = perms.get(uid)
                if not items:
                    items = []
                    perms[uid] = items
                items.append({'id':str(row['permid']), 'name':row['name'], 'info':row['info']})

            # 获取角色
            sql = "select up.userid as userid, up.roleid as roleid, r.name as name, r.info as info from user_perm as up,roles as r " \
                  "where up.userid in (%s) and up.roleid=r.id" % (useridstr)

            ret = conn.query(sql)
            log.debug('roles:%s', ret)
            
            for row in ret:
                uid = row['userid']
                items = roles.get(uid)
                if not items:
                    items = []
                    roles[uid] = items
                items.append({'id':str(row['roleid']), 'name':row['name'], 'info':row['info']})


        pdata = page.pagedata.data
        for row in pdata:
            for k in ['password']:
                row.pop(k)
            row['group'] = groups.get(int(row['id']), [])
            row['perm'] = perms.get(int(row['id']), [])
            row['role'] = roles.get(int(row['id']), [])
            row['id'] = str(row['id'])
            if row['extend']:
                row['extend'] = json.loads(row['extend'])


        pagedata = {
            'page':page.page, 
            'pagesize':page.page_size, 
            'pagenum':page.pages, 
            'data':pdata,
        }
        return OK, pagedata

    @with_validator([
        F('username'), 
        F('password'), 
        F('mobile', T_MOBILE),
        F('status', T_INT), 
        F('id', T_INT), 
        F('extend'),
    ]) 
    def modify(self):
        # modify username/status/password/extend
        userid_in = self.data.get('id', 0)
        isadmin = self.ses.get('isadmin', 0)
        userid  = self.ses.get('userid', 0)
        
        if userid_in and userid != userid_in:
            if not isadmin:
                return ERR_PERM, 'permission deny'
            else:
                userid = userid_in
        
        values = {}
        where  = {'id':userid}
       
        for k in ['username', 'password', 'extend', 'status', 'mobile']:
            v = self.data.get(k)
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
            return ERR_PARAM, 'not modify'

        values['utime'] = DBFunc("UNIX_TIMESTAMP(now())")

        with get_connection(self.dbname) as conn:
            ret = conn.update(self.table, values, where)
            if ret != 1:
                return ERR_PARAM, 'condition error'

            ret = conn.select_one(self.table, where={'id':userid}, 
                    fields="id,username,mobile,status,ctime,utime")

        return OK, ret

    @with_validator([
        F('groupid', T_INT, must=True),
        F('userid', T_INT),
    ])
    def group_join(self):
        isadmin = self.ses['isadmin']
        userid = self.ses['userid']
        in_userid = self.data.get('userid')
        
        if in_userid:
            if not isadmin:
                return ERR_PERM, 'permission deny'
            else:
                userid = in_userid
        
        groupid = self.data.get('groupid')
       
        t = int(time.time())
        with get_connection(self.dbname) as conn:
            data = {
                'id': createid.new_id64(conn=conn),
                'userid':userid,
                'groupid':groupid,
                'ctime':t,
                'utime':t,
            }
            ret = conn.insert('user_group', data)
            if ret != 1:
                return ERR_DB, 'error'

            ret = conn.select_one('user_group', where={'id':data['id']})
            for k in ['id','userid','groupid']:
                ret[k] = str(ret[k])
            return OK, ret


    @with_validator([F('groupid', T_INT, must=True)])
    def group_quit(self):
        isadmin = self.ses.get('isadmin', 0)
        groupid = self.data.get('groupid')
        #userid = self.ses['userid']

        where = {
            'groupid':groupid,
        }
        if not isadmin:
            where['userid'] = self.ses['useid']

        with get_connection(self.dbname) as conn:
            ret = conn.delete('user_group', where=where)
            return OK, ret

    @with_validator([
        F('permid', T_INT, default=0), 
        F('roleid', T_INT, default=0),
        F('userid', T_INT),
    ])
    def perm_give(self):
        isadmin = self.ses.get('isadmin', 0)
        userid = self.ses['userid']
        in_userid = self.data.get('userid')
        
        if in_userid:
            if not isadmin:
                return ERR_PERM, 'permission deny'
            else:
                userid = in_userid
 
        roleid = self.data.get('roleid')
        permid = self.data.get('permid')
            
        items = []
        for k in ['roleid', 'permid']:
            v = self.data.get(k)
            if not v:
                continue
            log.debug('%s: %s', k, v)
            if isinstance(v, (list,tuple)):
                for one in v:
                    data = {'roleid':0, 'permid':0}
                    data[k] = one
                    items.append(data)
            else:
                data = {'roleid':0, 'permid':0}
                data[k] = v
                items.append(data)

        t = int(time.time())
        with get_connection(self.dbname) as conn:
            ids = []
            for item in items:
                data = {
                    'id': createid.new_id64(conn=conn),
                    'userid':userid,
                    'roleid':item['roleid'],
                    'permid':item['permid'],
                    'ctime':t,
                    'utime':t,
                }
                ids.append(data['id'])

                ret = conn.insert('user_perm', data)
                if ret != 1:
                    return ERR_DB, 'error'

            ret = conn.select('user_perm', where={'id':('in', ids)})
            for row in ret:
                for k in ['id','userid','roleid','permid']:
                    row[k] = str(row[k])

            return OK, ret


    @with_validator([
        F('permid', T_INT, default=0), 
        F('roleid', T_INT, default=0),
        F('userid', T_INT),
    ])
    def perm_take(self):
        isadmin = self.ses.get('isadmin', 0)
        userid = self.data.get('userid', 0)
        #userid = self.ses.get('userid', 0)

        where = {}
        if isadmin and userid:
            where['userid'] = userid
        else:
            where['userid'] = self.ses.get('userid', 0)

        for k in ['roleid','permid']:
            v = self.data.get(k)
            if v:
                if isinstance(v, (list,tuple)):
                    where[k] = ('in', v)
                else:
                    where[k] = v

        with get_connection(self.dbname) as conn:
            ret = conn.delete('user_perm', where=where)
            return OK, {}


class User (UserBase):
    session_nocheck = [
        '/uc/v1/user/signup',
        '/uc/v1/user/signup_3rd',
        '/uc/v1/user/signin',
        '/uc/v1/user/signin_3rd',
        '/uc/v1/user/signauto_3rd',
    ]

    def query(self):
        data = self.req.input()
        if data.get('id'):
            return self.get_user_info()
        else:
            return self.get_user_list()

    def create(self):
        return self.signup()

    def delete(self):
        return ERR_PARAM, 'not support' 

    def error(self, data):
        self.fail(ERR_PARAM)

    def input(self):
        data = self.req.input()
        if data:
            return data
        return self.req.inputjson()


 

      
