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
import requests
from userbase import *
import utils
from ucdefines import *
import opensdk
import config


log = logging.getLogger()


def get_openid(code, appid):
    appinfo = config.OPENUSER_ACCOUNT[appid]
    if not appinfo:
        log.info('not found appinfo with appid:%s', appid)
        return None

    plat = appinfo['plat']

    if plat == 'wx':
        pass
    elif plat == 'wxmicro':
        url = 'https://api.weixin.qq.com/sns/jscode2session?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code' \
            % (appinfo['appid'], appinfo['secret'], code)
        r = requests.get(url) 
        obj = r.json()
        log.debug('get openid return: %s', json.dumps(obj))
        openid = obj.get('openid')
        return openid
    elif palt == 'alipay':
        pass




class Ping (BaseHandler):
    dbname = config.DBNAME
    url_public = [
        '/uc/v1/ping',
    ]

    def GET(self):
        data = {'time':int(time.time()), 'content':'pong'}
        self.succ(data)


class UserBase (BaseHandler):
    table  = 'users'
    dbname = config.DBNAME

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
   
    # 登录
    @with_validator_dict([
        F('username'), 
        F('password', must=True), 
        F('email', T_EMAIL), 
        F('mobile', T_MOBILE),
    ])
    def signin(self):
        try:
            username = self.data.get('username')
            password = self.data.get('password')
            email    = self.data.get('email')
            mobile   = self.data.get('mobile')

            if not username and not email and not mobile:
                self.fail(ERR, 'username/email/mobile至少需要填写一项')
                return

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
                    log.debug('login key %s error', login_key)
                    self.fail(ERR_USER, login_key + ' 错误')
                    return

                # password:   sha1$123456$AJDKLJDLAKJKDLSJKLDJALASASASA
                px = ret['password'].split('$')
                pass_enc = create_password(password, int(px[1]))
                if ret['password'] != pass_enc:
                    log.debug('password error')
                    self.fail(ERR_AUTH, '用户名或密码错误')
                    return

                if ret['status'] != STATUS_OK:
                    log.debug('status error')
                    self.fail(ERR_AUTH, "用户状态错误")
                    return
     
                conn.update(self.table, {'logtime':DBFunc('now()')}, 
                        where={'id':ret['id']})

                retcode, userinfo = self._get_user(ret['id'])
                log.debug('get user: %d %s', retcode, userinfo)

            self._signin_set(userinfo, ret)

            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            self.fail(ERR, 'Exception:' + str(e))
            return

    def _signin_set(self, userinfo, row):
        sesdata = {
            'userid':int(row['id']), 
            'username':row['username'], 
            'isadmin':row['isadmin'], 
            'status': userinfo['status'],
            'allperm':[ x['name'] for x in userinfo['allperm']],
        }
        self.ses.update(sesdata)

    # 通过第三方授权登录
    @with_validator_dict([
        F('appid', must=True), 
        F('code', must=True),
        F('openid'), 
    ])
    def open_signin(self):
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
                ret = conn.select_one('open_user', where, 'userid')
                if not ret:
                    return ERR_AUTH, 'apppid/openid error'

                userid = ret['userid']

                #log.debug('where:%s', where)
                ret = conn.select_one(self.table, {'id':userid}, "id,username,email,password,isadmin,status")
                log.debug('select:%s', ret)
                if not ret:
                    return ERR_USER, ' appid/openid not found'

                conn.update(self.table, {'logtime':DBFunc('now()')}, where={'id':userid})

            retcode, userinfo = self._get_user(ret['id'])
            
            self._signin_set(userinfo, ret)
            self.ses.update({
                'appid':appid,
                'openid':openid,
                'plat':config.OPENUSER_ACCOUNT[appid]['plat'],
            })

            #self.succ({'id':str(ret['id']), 'username':ret['username']})
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            self.fail(ERR, 'Exception:' + str(e))
            return


    # 用户注册
    @with_validator_dict([
        F('username'), 
        F('password', must=True), 
        F('email', T_EMAIL),
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
                'ctime': DBFunc('now()'),
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

            userinfo = self._signup_set(insertdata['id'])
          
            return OK, userinfo
        except Exception as e:
            log.error(traceback.format_exc())
            self.fail(ERR, 'error:' + str(e))
            return

    def _signup_set(self, userid):
        retcode, userinfo = self._get_user(userid)

        # 没有session才能创建新session
        if not self.ses:
            #self.create_session()
            log.debug('create sesssion:%s', self.ses.sid)
            sesdata = {
                'userid':int(userid), 
                'username':userinfo['username'], 
                'isadmin':0, 
                'status':userinfo['status'],
            }
            self.ses.update(sesdata)

        return userinfo

    # 绑定第三方平台账号
    @with_validator_dict([
        F('appid', must=True), 
        F('code', must=True), 
        F('id', T_INT), 
        F('openid'), 
    ])
    def bind(self):
        appid = self.data.get('appid')
        code  = self.data.get('code')
        userid= self.data.get('id')
        openid= self.data.get('openid')

        if not openid:
            openid = utils.get_openid(code, appid)
            if not openid:
                return ERR_AUTH, 'openid error'
            
        return self._bind_openuser(appid, openid, userid)

    def _bind_openuser(self, appid, openid, userid=None):
        try:
            where = {
                'appid':appid,
                'openid':openid,
            }

            lastid = -1
            with get_connection(self.dbname) as conn:
                ret = conn.select_one('open_user', where=where, fields='userid')
                if ret:
                    return ERR_USER, 'user exist'

                ret = conn.select_one(self.table, where={'id':userid}, fields='id')
                if not ret:
                    return ERR_USER, 'user error'

                openuser_data = {
                    'id': createid.new_id64(conn=conn),
                    'userid':user_data['id'],
                    'appid':appid,
                    'openid':openid,
                    'plat':config.OPENUSER_ACCOUNT[appid]['plat'],
                    'ctime':DBFunc('now()'),
                }
                conn.insert('open_user', openuser_data)
          
            return OK, {'userid':userid, 'appid':appid, 'openid':openid}
        except Exception as e:
            log.error(traceback.format_exc())
            self.fail(ERR, 'error:' + str(e))
            return


    # 获取用户信息
    @with_validator_dict([F('id', T_INT),])
    def get_user_info(self):
        userid_in = self.data.get('id', 0)
        userid  = self.ses.get('userid', 0)
        isadmin = self.ses.get('isadmin', 0)
       
        # 非超级管理员，只能获取自己的信息
        if userid_in and  userid != userid_in:
            if not isadmin:
                log.info('userid_in:%d userid:%d isadmin:%d', userid_in, userid, isadmin)
                return ERR_PERM, 'permission deny'
            else:
                userid = userid_in

        retcode, data = self._get_user(userid)
        return retcode, data

    # 获取用户信息，内部调用
    def _get_user(self, userid):
        userid = int(userid)

        where = {'id':userid}
        user = None
        groups = None
        fields ='id,username,password,email,mobile,head,score,stage,ctime,' \
            'utime,logtime,regip,status,isadmin,extend'
        with get_connection(self.dbname) as conn:
            user = conn.select_one(self.table, where, fields=fields)
            if not user:
                return ERR_USER, 'not have user info'
            # 查询用户所在的组
            groups = conn.query('select g.id as id,g.name as name from user_group ug, groups g where g.id=ug.groupid and ug.userid=%d' % userid)
            if not groups:
                groups = []
            user['group'] = groups     

            user['role'] = []
            user['perm'] = []
            # 所有权限，包括从角色里展开的权限
            user['allperm'] = []
            
            # 查询用户所有的权限和角色
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
        else:
            user['extend'] = {}

        #for k in ['group','role','perm','allperm']:
        #    convert_data(user[k])

        return OK, user

    # 获取用户列表，只有超级管理员可以
    @with_validator_dict([
        F('page',T_INT,default=1), 
        F('pagesize',T_INT,default=20),
        F('username'),
        F('mobile', T_MOBILE),
        F('ctime', T_LIST, count=2, subs=[
            F('_', T_DATETIME)
        ]),
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
        log.debug('ctime: %s', ctime)
        if ctime:
            where['ctime'] = ['between', ctime]

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

            if ret:
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
           
            if ret:
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
           
            if ret:
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
            'pagecount':page.pages, 
            'data':pdata,
        }
        return OK, pagedata

    # 修改用户信息
    @with_validator_dict([
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
       
        # 此接口只允许修改自己的信息, 除非是超级管理员
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

        values['utime'] = DBFunc("now()")

        with get_connection(self.dbname) as conn:
            ret = conn.update(self.table, values, where)
            if ret != 1:
                return ERR_PARAM, 'condition error'

            ret = conn.select_one(self.table, where={'id':userid}, 
                    fields="id,username,mobile,status,ctime,utime")

        return OK, ret

    # 把用户加入某个用户组
    @with_validator_dict([
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
       
        with get_connection(self.dbname) as conn:
            data = {
                'id': createid.new_id64(conn=conn),
                'userid':userid,
                'groupid':groupid,
                'ctime':DBFunc('now()'),
                'utime':DBFunc('now()'),
            }
            ret = conn.insert('user_group', data)
            if ret != 1:
                return ERR_DB, 'error'

            ret = conn.select_one('user_group', where={'id':data['id']})
            for k in ['id','userid','groupid']:
                ret[k] = str(ret[k])
            return OK, ret

    # 把用户从用户组中删除
    @with_validator_dict([F('groupid', T_INT, must=True)])
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

    # 分配权限
    @with_validator_dict([
        F('permid', T_LIST, subs=[
            F('_', T_INT),
        ]), 
        F('roleid', T_LIST, subs=[
            F('_', T_INT),
        ]),
        F('userid', T_INT),
    ])
    def perm_alloc(self):
        isadmin = self.ses.get('isadmin', 0)
        userid = self.ses['userid']
        in_userid = self.data.get('userid')
        
        if in_userid:
            if not isadmin:
                return ERR_PERM, 'permission deny'
            else:
                userid = in_userid
 
        roleid = self.data.get('roleid', 0)
        permid = self.data.get('permid', 0)
            
        items = []
        for k in ['roleid', 'permid']:
            v = self.data.get(k)
            if not v:
                continue
            if isinstance(v, (list,tuple)):
                for a in v:
                    data = {'roleid':0, 'permid':0}
                    data[k] = a
                    items.append(data)
            else:
                data = {'roleid':0, 'permid':0}
                data[k] = v
                items.append(data)

        with get_connection(self.dbname) as conn:
            ids = []
            for item in items:
                data = {
                    'id': createid.new_id64(conn=conn),
                    'userid':userid,
                    'roleid':item['roleid'],
                    'permid':item['permid'],
                    'ctime':DBFunc('now()'),
                    'utime':DBFunc('now()'),
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

    
    # 取消权限
    @with_validator_dict([
        F('permid', T_LIST, subs=[F('_', T_INT)]), 
        F('roleid', T_LIST, subs=[F('_', T_INT)]),
        F('userid', T_INT),
    ])
    def perm_cancel(self):
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
                where[k] = ('in', v)

        with get_connection(self.dbname) as conn:
            ret = conn.delete('user_perm', where=where)
            return OK, {}


class User (UserBase):
    url_public = [
        '/uc/v1/user/signin',
        '/uc/v1/user/signup',
        '/uc/v1/user/open_signin',
    ]

    def query(self):
        data = self.input()
        log.debug('query data: %s', data)
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



def test_openid():
    ret = get_openid(sys.argv[1], 'wx27edcac7e40b6688')
    print(ret)
 


