# coding: utf-8
import os, sys
CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(CWD))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(CWD)), 'conf'))
import json
import urllib
import urllib.request
import pprint
from zbase3.base import dbpool, logger
import config_debug
import config
import createpass
import datetime, time
import hashlib
import urllib
import urllib.parse
import traceback

log = logger.install('stdout')
dbpool.install(config_debug.DATABASE)


SERVER = '%s:%d' % (config.HOST, config.PORT) 
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    s.connect((config.HOST, config.PORT))
except:
    SERVER = '%s:%d' % (config_debug.HOST, config_debug.PORT)

class MyRequest (urllib.request.Request):
    method = 'POST'

cookie = ''

def sign(s, secret):
    s = s + secret.encode()
    x = hashlib.md5()
    x.update(s)
    return x.hexdigest()

def request(url, values=None, method='POST', **options):
    global cookie
    print('\33[0;33m' + '='*30 + '\33[0m')
    print('>>>>')
    print(method, url)
    print('values:', values)
  
    #data = None
    #if values:
    #    data = urllib.parse.urlencode(values)
    data = json.dumps(values).encode()
    headers = {
        'User-Agent': 'testclient',
        #'Cookie': 'sid=%d'
        'X-APPID': options.get('appid', ''),
        'X-SIGN': sign(data, options.get('secret', '')),
    }
    if cookie:
        headers['Cookie'] = cookie
    #req = MyRequest(url, data, headers)

    #data = urllib.parse.urlencode(values).encode()
    req = MyRequest(url, data, headers=headers)
    #req.method = method
    print('<<<<')

    ret = {}
    try:
        resp = urllib.request.urlopen(req, data=data)
    except Exception as e:
        #print(e.code)
        print('request error:', e)
        traceback.print_exc()
    else:
        print('code:', resp.code)
        #print resp.headers
        respdata = resp.read()
        if resp.code >= 400:
            print('data:', respdata)
            raise ValueError('request error: {0} {1}'.format(resp.code, respdata))
        
        c = resp.headers.get('Set-Cookie')
        if c:
            cookie = c.split(';')[0]
            print('cookie:', cookie)

        print(respdata)
        ret = json.loads(respdata)
        #pprint.pprint(ret)
        print(json.dumps(ret, indent=2))

    return ret


class Request():
    def __init__(self, appid='', secret=''):
        self.appid = appid
        self.secret = secret

    def go(self, url, values=None):
        return request(url, values, appid=self.appid, secret=self.secret)

class Base:
    def make_args(self, url, args):
        params = []

        print('args:', args)
        for k,v in args.items():
            if isinstance(v, bytes):
                params.append('%s=%s' % (k, v))
            elif isinstance(v, str):
                if ',' in v and '__' not in k:
                    params.append('%s__in=%s' % (k, urllib.parse.quote(v.encode('utf-8'))))
                else:
                    params.append('%s=%s' % (k, urllib.parse.quote(v.encode('utf-8'))))
            else:
                params.append('%s=%s' % (k, str(v)))
        if params:
            url = url + '?' + '&'.join(params)

        return url


class User (Base):
    def __init__(self, mobile='', userid='0', appid='', out_appid=''):
        self.userid = int(userid)
        self.mobile = mobile

        global SERVER
        self.prefix_url = 'http://%s/uc/v1/user' % SERVER
        self.appid  = appid
        self.secret = '0000000000000000'
        self.out_appid  = out_appid

        self.req = Request(self.appid, self.secret)


    def clear(self):
        ret = self.user_db()
        if self.out_appid:
            sqls = ["delete from open_user where appid='%s'" % (self.out_appid) ]
        else:
            sqls = [
                "delete from users where id=%d" % (self.userid),
                "delete from login_record where userid=%d" % (self.userid),
                "delete from open_user where userid=%d" % (self.userid),
                "delete from user_group where userid=%d" % (self.userid),
                "delete from user_perm where userid=%d" % (self.userid),
            ]

            if self.appid:
                sqls += ["delete from apps where appid={}".format(self.appid)]



        with dbpool.get_connection('usercenter') as conn:
            for x in sqls:
                conn.execute(x)

    def set_admin(self, v=1):
        with dbpool.get_connection('usercenter') as conn:
            conn.update('users', {'isadmin':v}, where={'mobile':self.mobile})

    def create(self):
        data = {
            'id': self.userid, 
            'mobile': self.mobile,
            'username': 'zhaowei%d' % self.userid,
            'password': createpass.create_password('123456'),
            'status': 2,
            'ctime': dbpool.DBFunc('now()'),
        }
        with dbpool.get_connection('usercenter') as conn:
            ret = conn.insert('users', data)
            return ret

    def create_app(self):
        appdata = {
            'appid':'1234567890',
            'userid':self.userid,
            'secret':'0000000000000000',
            'ctime': dbpool.DBFunc('now()'),
        }
        with dbpool.get_connection('usercenter') as conn:
            ret = conn.insert('apps', appdata)
            return ret

    def user_db(self):
        with dbpool.get_connection('usercenter') as conn:
            ret = conn.select_one('users', where={'mobile':self.mobile})
            if ret:
                self.userid = ret['id']
            return ret

    def get_last(self, table):
        where = {}
        if table == 'users':
            where['id'] = self.userid
        else:
            where['userid'] = self.userid
        with dbpool.get_connection('usercenter') as conn:
            ret = conn.select_one(table, where=where, other=' order by id desc limit 1')
            return ret

    def signup(self): 
        url = self.prefix_url + '/signup'
        data = {
            'mobile':self.mobile,
            'password':'123456',
            'username':'zhaowei%d' % (self.userid),
            'email':'zhaowei%d@qq.com' % (self.userid)
        }
        return request(url, data, appid=self.appid, secret=self.secret)

    def bind(self, code): 
        url = self.prefix_url + '/bind'
        data = {
            'appid':self.appid,
            'code':code,
        }
        return request(url, data, appid=self.appid, secret=self.secret)

    def signin(self):
        url = self.prefix_url + '/signin'
        data = {
            'password': '123456',
            'mobile':self.mobile,
        }
        return request(url, data, appid=self.appid, secret=self.secret)

    def open_signin(self, code):
        url = self.prefix_url + '/open_signin'
        data = {
            'appid':self.appid,
            'code':code
        }
        return request(url, data, appid=self.appid, secret=self.secret)

    def query(self, **args):
        url = self.prefix_url + '/query'
        #return request(self.make_args(url, args), args)
        return request(url, args, appid=self.appid, secret=self.secret)

    def modify(self, **args):
        url = self.prefix_url + '/modify'
        return request(url, args, appid=self.appid, secret=self.secret)
    
    def group_join(self, groupid):
        url = self.prefix_url + '/group_join'
        data = {
            'groupid':int(groupid),
        }
        return request(url, data, appid=self.appid, secret=self.secret)

    def group_quit(self, groupid):
        url = self.prefix_url + '/group_quit'
        data = {
            'groupid':int(groupid),
        }
        return request(url, data, appid=self.appid, secret=self.secret)

    def perm_alloc(self, **args):
        url = self.prefix_url + '/perm_alloc'
        return request(url, args, appid=self.appid, secret=self.secret)

    def perm_cancel(self, **args):
        url = self.prefix_url + '/perm_cancel'
        return request(url, args, appid=self.appid, secret=self.secret)


class Group (Base):
    def __init__(self, user):
        global SERVER
        self.user = user
        self.prefix_url = 'http://%s/uc/v1/group' % SERVER
        self.fields = ['name', 'info', 'parentid']
        self.delete_sqls = ["delete from groups"]

    def clear(self):
        with dbpool.get_connection('usercenter') as conn:
            for x in self.delete_sqls:
                conn.execute(x)

    def create(self, **args):
        url = self.prefix_url + '/create'
        return request(url, args, appid=self.user.appid, secret=self.user.secret)

    def delete(self, xid):
        url = self.prefix_url + '/delete'
        data = {
            'id':int(xid),
        }
        return request(url, data, appid=self.user.appid, secret=self.user.secret)

    def modify(self, xid, **args):
        url = self.prefix_url + '/modify'
        
        data = {}
        if ',' in xid:
            #data['id__in'] = xid
            data['id'] = xid.split(',')
        else:
            data['id'] = xid
        data.update(args)

        return request(url, data, appid=self.user.appid, secret=self.user.secret)

    def query(self, **args):
        url = self.prefix_url + '/query'
            
        #data = {}
        #for k in self.fields:
        #    if k in args:
        #        data[k] = args[k] 
        return request(url, args, appid=self.user.appid, secret=self.user.secret)



class Role (Group):
    def __init__(self, user):
        global SERVER
        self.user = user
        self.prefix_url = 'http://%s/uc/v1/role' % SERVER
        self.fields = ['name', 'info']
        self.delete_sqls = ["delete from roles"]

    def perm_alloc(self, **args):
        url = self.prefix_url + '/perm_alloc'        
        return request(url, args, appid=self.user.appid, secret=self.user.secret)
        
    def perm_cancel(self, **args):
        url = self.prefix_url + '/perm_cancel'        
        return request(url, args, appid=self.user.appid, secret=self.user.secret)
 


class Perm (Group):
    def __init__(self, user):
        global SERVER
        self.user = user
        self.prefix_url = 'http://%s/uc/v1/perm' % SERVER
        self.fields = ['name', 'info']
        self.delete_sqls = ["delete from perms"]


u = User('18800006666', 6666, '1234567890')


def test_user_create():
    global u
    
    u.clear()
    u.create()
    u.create_app()

    #ret = u.signup()
    #print(ret)

    ret = u.signin()
    print(ret)
    userid = ret['data']['id']

    u.user_db()
    last = u.get_last('users')
    print('last:', last['id'], ' signup:', ret['data']['id'])
    assert last['id'] == int(ret['data']['id'])
    print('='*20, 'signup ok', '='*20)

    print(u.query(id=userid))

def test_user_list():
    global u

    userinfo = u.user_db()
    u.set_admin(1)

    ret = u.signin()
    userid = ret['data']['id']

    u.query(id=userid)
    ret = u.query(mobile=u.mobile)
    assert len(ret['data']['data']) == 1

    ret = u.query(username=userinfo['username'])
    assert len(ret['data']['data']) == 1

    # 前推10秒, 后推200秒之内的数据
    fromdt = userinfo['ctime'] - datetime.timedelta(seconds=10)
    todt = fromdt + datetime.timedelta(seconds=200)

    s = '%s,%s' % (str(fromdt)[:19], str(todt)[:19])

    #ret = u.query(ctime__bt=s)
    #ret = u.query(ctime=['bt', [str(fromdt)[:19], str(todt)[:19]]])
    ret = u.query(ctime=[str(fromdt)[:19], str(todt)[:19]])
    assert len(ret['data']['data']) == 1

    #from2 = userinfo['ctime'] - 86400*365
    #fromdt2 = datetime.datetime.fromtimestamp(from2)
    fromdt2 = userinfo['ctime'] - datetime.timedelta(days=365)
    s2 = '%s,%s' % (str(fromdt2)[:19], str(todt)[:19])
    #ret = u.query(ctime__bt=s2)
    #ret = u.query(ctime=['bt', [str(fromdt2)[:19], str(todt)[:19]]])
    ret = u.query(ctime=[str(fromdt2)[:19], str(todt)[:19]])
    assert len(ret['data']['data']) >= 2
    #assert len(ret['data']['data']) >= 1


def test_user_modify():
    global u

    userinfo = u.user_db()

    ret = u.signin()
    userid = ret['data']['id']

    old_status = userinfo['status']
    new_status = 2
    ret = u.modify(id=userid, status=new_status)

    assert ret['data']['status'] == new_status


    old_pwd = userinfo['password']
    new_pwd = '123456'

    ret = u.modify(id=userid, password=new_pwd)
    newuser = u.user_db()
    assert old_pwd != newuser['password']




def test_user_query():
    global u

    userinfo = u.user_db()

    ret = u.signin()
    userid = ret['data']['id']

    ret = u.query(id=userid)
    assert ret['data']['id'] == str(userinfo['id'])

    ret = u.query(id=userinfo['id'])
    assert ret['data']['id'] == str(userinfo['id'])

    ret = u.query(id=1)
    assert ret['data']['id'] == '1'



def test_group():
    global u

    ret = u.signin()
    userid = ret['data']['id']

    gp = Group(u)
    gp.clear()
    ret = gp.create(name="组1", info="测试组1", parentid=0)
    ret = gp.create(name="组2", info="测试组2", parentid=0)
    ret = gp.create(name="组3", info="测试组3", parentid=0)


    gpid = ret['data']['id']

    gp.modify(gpid, name='组11', info='测试组11111')

    rows = gp.query()

    allids = ','.join([ x['id'] for x in rows['data']['data']])

    gp.modify(allids, info='haha')

    rows = gp.query()

    for row in rows['data']['data']:
        assert row['info'] == 'haha'

    one = rows['data']['data'][0]

    rows = gp.query(name='组2')
    assert len(rows['data']['data']) == 1

    ret = u.group_join(one['id'])
    groupid = ret['data']['groupid']

    ret = u.query(id=userid)
    rows = ret['data']['group'] 
    groupdict =  set([ x['id'] for x in rows])
    print('groupid:', groupid, type(groupid))
    assert groupid in groupdict

    u.group_quit(one['id'])
    ret = u.query(id=userid)
    rows = ret['data']['group'] 
    groupdict =  set([ x['id'] for x in rows])

    assert groupid not in groupdict


def test_role():
    global u

    ret = u.signin()
    userid = ret['data']['id']

    u.query(id=userid)

    r = Role(u)
    r.clear()
    
    ret = r.create(name="角色1", info="测试角色1")
    ret = r.create(name="角色2", info="测试角色2")
    ret = r.create(name="角色3", info="测试角色3")

    rid = ret['data']['id']

    r.modify(rid, name='角色11', info='测试角色11111')

    rows = r.query()

    allids = ','.join([ x['id'] for x in rows['data']['data']])

    r.modify(allids, info='haha')

    rows = r.query()

    for row in rows['data']['data']:
        assert row['info'] == 'haha'

    one = rows['data']['data'][0]

    rows = r.query(name='角色2')
    assert len(rows['data']['data']) == 1

    ret = u.perm_alloc(roleid=[one['id'],])
    roleid = ret['data'][0]['roleid']

    ret = u.query(id=userid)
    rows = ret['data']['role'] 
    roledict =  set([ x['id'] for x in rows])

    assert roleid in roledict

    u.perm_cancel(roleid=[one['id'],])
    ret = u.query(id=userid)
    rows = ret['data']['role'] 
    roledict =  set([ x['id'] for x in rows])

    assert roleid not in roledict

    u.perm_alloc(roleid=allids.split(','))
    ret = u.query(id=userid)
    rows = ret['data']['role'] 
    roledict =  set([ x['id'] for x in rows])

    assert len(roledict) == allids.count(',')+1


def test_perm():
    global u

    ret = u.signin()
    userid = ret['data']['id']
    u.query(id=userid)

    r = Perm(u)
    r.clear()
    
    ret = r.create(name="perm_view", info="查看权限")
    ret = r.create(name="perm_mod", info="修改权限")
    ret = r.create(name="group_view", info="创建组")
    ret = r.create(name="group_mod", info="修改组")

    rid = ret['data']['id']

    r.modify(rid, name='xxx_view', info='测试权限11111')

    rows = r.query()

    allids = ','.join([ x['id'] for x in rows['data']['data']])

    r.modify(allids, info='haha')

    rows = r.query()

    for row in rows['data']['data']:
        assert row['info'] == 'haha'

    one = rows['data']['data'][0]

    rows = r.query(name='perm_mod')
    assert len(rows['data']['data']) == 1

    ret = u.perm_alloc(permid=[one['id'],])
    permid = ret['data'][0]['permid']

    ret = u.query(id=userid)
    rows = ret['data']['perm'] 
    permdict =  set([ x['id'] for x in rows])

    assert permid in permdict

    u.perm_cancel(permid=[one['id'],])
    ret = u.query(id=userid)
    rows = ret['data']['perm'] 
    permdict =  set([ x['id'] for x in rows])

    assert permid not in permdict


    ret = u.perm_alloc(permid=allids.split(','))
    assert len(ret['data']) == allids.count(',')+1

    ret = u.query(id=userid)
    assert len(ret['data']['perm']) == allids.count(',')+1

    ret = u.perm_cancel(permid=allids.split(','))
    ret = u.query(id=userid)
    assert len(ret['data']['perm']) == 0

def test_simple():
    global u
    
    #u.create()
    
    ret = u.signin()
    userid = ret['data']['id']

    #u.query(userid)
    #u.query()

    #r = Role()
    #ret = r.query()
    #roleid = ret['data']['data'][0]['id']
    #r.query(useridroleid)    

    #r.addperm(id=roleid, permid=6531811927155317021)
    #ret = r.query(useridroleid)    

    #rolepermid= ret['data']['perm'][-1]['id']
    #r.delperm(id=roleid, permid=6531811927155317021)

    #u2 = User('18800001111', 8888)
    #u2.clear()
    #u2.signup()
    #u2.query()

    #u.query()

    #g = Group()
    #ret = g.query()
    #g.query(useridret['data']['data'][0]['id'])

    #u = User(appid='wx27edcac7e40b6688')
    #u.clear()
    #u.signup3rd('081Q3Ccx0qOOQc1rfNax0N6Hcx0Q3CcP')
    #u.login_reg_3rd('081okA9N1hTnv71OfhbN1x1A9N1okA93')

    pass

def test_sign():
    global u
    
    #u.create()
    
    ret = u.signin()
    userid = ret['data']['id']


def main():
    name = ''
    if len(sys.argv) == 2:
        name = sys.argv[1]

    if not name or name == 'test_user_create':
        print('='*6, 'test_user_create', '='*6)
        test_user_create()

    for a in globals().keys():
        if not a.startswith('test'):
            continue
        if a == 'test_user_create':
            continue
        if name:
            if name == a:
                print('='*6, '<'*6, a, '>'*6, '='*6)
                globals()[a]()
        else:
            print('='*6, '<'*6, a, '>'*6, '='*6)
            globals()[a]()



if __name__ == '__main__':
    main()


