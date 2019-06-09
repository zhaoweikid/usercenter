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
import urllib
import urllib.parse

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
    method = 'GET'
    def get_method(self):
        return self.method

cookie = ''

def request(url, method, values=None):
    global cookie
    print('\33[0;33m' + '='*30 + '\33[0m')
    print('>>>>')
    print(method, url)
    print('values:', values)
  
    data = None
    if values:
        data = urllib.parse.urlencode(values)
    headers = {
        'User-Agent': 'testclient',
        #'Cookie': 'sid=%d'
    }
    if cookie:
        headers['Cookie'] = cookie
    #req = MyRequest(url, data, headers)
    req = MyRequest(url, data, headers=headers)
    req.method = method
    print('<<<<')

    ret = {}
    try:
        resp = urllib.request.urlopen(req)
    except Exception as e:
        print(e.code)
        print(e)
    else:
        print(resp.code)
        #print resp.headers
        
        c = resp.headers.get('Set-Cookie')
        if c:
            cookie = c.split(';')[0]
            print('cookie:', cookie)

        s = resp.read()
        print(s)
        ret = json.loads(s)
        #pprint.pprint(ret)
        print(json.dumps(ret, indent=2))

    return ret

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
    def __init__(self, mobile='', userid='0', appid=''):
        self.userid = int(userid)
        self.mobile = mobile

        global SERVER
        self.prefix_url = 'http://%s/uc/v1/user' % SERVER
        self.appid  = appid


    def clear(self):
        ret = self.user_db()
       
        if self.appid:
            sqls = ["delete from openuser where appid='%s'" % (self.appid) ]
        else:
            sqls = [
                "delete from users where id=%d" % (self.userid),
                "delete from login_record where userid=%d" % (self.userid),
                "delete from openuser where userid=%d" % (self.userid),
                "delete from user_group where userid=%d" % (self.userid),
                "delete from user_perm where userid=%d" % (self.userid),
            ]

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
            'ctime': dbpool.DBFunc('FROM_UNIXTIME(now())'),
        }
        with dbpool.get_connection('usercenter') as conn:
            ret = conn.insert('users', data)
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
        url = self.prefix_url + '/signup?mobile=%s&password=123456&username=zhaowei%d&email=zhaowei%d@qq.com' % \
            (self.mobile, self.userid, self.userid)

        return request(url, 'POST')


    def signup3rd(self, code): 
        url = self.prefix_url + '/signup3rd?appid=%s&code=%s' % \
            (self.appid, code)

        return request(url, 'POST')

    def login(self):
        url = self.prefix_url + '/login?password=123456&mobile=%s' % (self.mobile)
        return request(url, 'GET')


    def login3rd(self, code):
        url = self.prefix_url + '/login3rd?appid=%s&code=%s' % (self.appid, code)
        return request(url, 'GET')

    def login_reg_3rd(self, code):
        url = self.prefix_url + '/login_reg_3rd?appid=%s&code=%s' % (self.appid, code)
        return request(url, 'POST')



    def q(self, userid=None):
        url = self.prefix_url + '/q'
        if userid:
            url += '?userid=' + str(userid)
        return request(url, 'GET')

    def list(self, **args):
        url = self.prefix_url + '/list'        
        return request(self.make_args(url, args), 'GET')
    
    def mod(self, **args):
        url = self.prefix_url + '/mod'
        return request(self.make_args(url, args), 'POST')
    
    def addgroup(self, groupid):
        url = self.prefix_url + '/addgroup?groupid=%d' % int(groupid)
        return request(url, 'POST')

    def delgroup(self, groupid):
        url = self.prefix_url + '/delgroup?groupid=%d' % int(groupid)
        return request(url, 'POST')

    def addperm(self, **args):
        url = self.prefix_url + '/addperm'

        #if permid:
        #    url += "?permid=%d" % int(permid)
        #elif roleid:
        #    url += "?roleid=%d" % int(roleid)
        #return request(url, 'POST')

        return request(self.make_args(url, args), 'POST')


    def delperm(self, **args):
        url = self.prefix_url + '/delperm'

        #if permid:
        #    url += "?permid=%d" % int(permid)
        #elif roleid:
        #    url += "?roleid=%d" % int(roleid)
        #return request(url, 'POST')

        return request(self.make_args(url, args), 'POST')


class Group (Base):
    def __init__(self):
        global SERVER
        self.prefix_url = 'http://%s/uc/v1/group' % SERVER
        self.fields = ['name', 'info', 'parentid']
        self.delete_sqls = ["delete from groups"]

    def clear(self):
        with dbpool.get_connection('usercenter') as conn:
            for x in self.delete_sqls:
                conn.execute(x)

    def add(self, **args):
        url = self.prefix_url + '/add'
        data = {}

        for k in self.fields:
            data[k] = args[k]
        return request(self.make_args(url, data), 'POST')

    def delete(self, xid):
        url = self.prefix_url + '/del?id=' + str(xid)
        return request(self.make_args(url, data), 'POST')

    def mod(self, xid, **args):
        url = self.prefix_url + '/mod'
        data = {}
        
        #if ',' in xid:
        #    data['id__in'] = xid
        #else:
        #    data['id'] = xid

        data['id'] = xid
        for k in self.fields:
            if k in args:
                data[k] = args[k]

        return request(self.make_args(url, data), 'POST')

    def q(self, xid):
        url = self.prefix_url + '/q?id=' + str(xid)
        return request(url, 'GET')

    def list(self, **args):
        url = self.prefix_url + '/list'
        data = {}
        
        for k in self.fields:
            if k in args:
                data[k] = args[k] 

        return request(self.make_args(url, data), 'GET')


class Role (Group):
    def __init__(self):
        global SERVER
        self.prefix_url = 'http://%s/uc/v1/role' % SERVER
        self.fields = ['name', 'info']
        self.delete_sqls = ["delete from roles"]

    def addperm(self, **args):
        url = self.prefix_url + '/addperm'        
        return request(self.make_args(url, args), 'GET')
        
    def delperm(self, **args):
        url = self.prefix_url + '/delperm'        
        return request(self.make_args(url, args), 'GET')
 


class Perm (Group):
    def __init__(self):
        global SERVER
        self.prefix_url = 'http://%s/uc/v1/perm' % SERVER
        self.fields = ['name', 'info']
        self.delete_sqls = ["delete from perms"]


u = User('18800006666', 6666)

def test_user_create():
    global u
    
    u.clear()
    #u.create()

    ret = u.signup()
    print(ret)

    ret = u.login()
    print(ret)

    u.user_db()
    last = u.get_last('users')
    print('last:', last['id'], ' signup:', ret['data']['id'])
    assert last['id'] == int(ret['data']['id'])
    print('='*20, 'signup ok', '='*20)

    print(u.q())

def test_user_list():
    global u

    userinfo = u.user_db()
    u.set_admin(1)

    ret = u.login()
    u.q()
    u.list()
    ret = u.list(mobile=u.mobile)
    assert len(ret['data']['data']) == 1

    ret = u.list(username=userinfo['username'])
    assert len(ret['data']['data']) == 1

    from1 = userinfo['ctime'] - 100 
    to1 = from1 + 200

    fromdt = datetime.datetime.fromtimestamp(from1)
    todt = datetime.datetime.fromtimestamp(to1)

    s = '%s,%s' % (str(fromdt)[:19], str(todt)[:19])

    ret = u.list(ctime__bt=s)
    assert len(ret['data']['data']) == 1

    from2 = userinfo['ctime'] - 1000000
    fromdt2 = datetime.datetime.fromtimestamp(from2)
    s2 = '%s,%s' % (str(fromdt2)[:19], str(todt)[:19])
    ret = u.list(ctime__bt=s2)
    assert len(ret['data']['data']) >= 2


def test_user_mod():
    global u

    userinfo = u.user_db()

    ret = u.login()

    old_status = userinfo['status']
    new_status = 2
    ret = u.mod(status=new_status)

    assert ret['data']['status'] == new_status


    old_pwd = userinfo['password']
    new_pwd = '123456'

    ret = u.mod(password=new_pwd)
    newuser = u.user_db()
    assert old_pwd != newuser['password']




def test_user_query():
    global u

    userinfo = u.user_db()

    ret = u.login()

    ret = u.q()
    assert ret['data']['id'] == str(userinfo['id'])

    ret = u.q(userid=userinfo['id'])
    assert ret['data']['id'] == str(userinfo['id'])

    ret = u.q(userid=1)
    assert ret['data']['id'] == '1'



def test_group():
    global u

    u.login()

    gp = Group()
    gp.clear()
    ret = gp.add(name="组1", info="测试组1", parentid=0)
    ret = gp.add(name="组2", info="测试组2", parentid=0)
    ret = gp.add(name="组3", info="测试组3", parentid=0)


    gpid = ret['data']['id']

    gp.mod(gpid, name='组11', info='测试组11111')

    rows = gp.list()

    allids = ','.join([ x['id'] for x in rows['data']['data']])

    gp.mod(allids, info='haha')

    rows = gp.list()

    for row in rows['data']['data']:
        assert row['info'] == 'haha'

    one = rows['data']['data'][0]

    rows = gp.list(name='组2')
    assert len(rows['data']['data']) == 1

    ret = u.addgroup(one['id'])
    groupid = ret['data']['groupid']

    ret = u.q()
    rows = ret['data']['group'] 
    groupdict =  set([ x['id'] for x in rows])

    assert groupid in groupdict

    u.delgroup(one['id'])
    ret = u.q()
    rows = ret['data']['group'] 
    groupdict =  set([ x['id'] for x in rows])

    assert groupid not in groupdict


def test_role():
    global u

    u.login()
    u.q()

    r = Role()
    r.clear()
    
    ret = r.add(name="角色1", info="测试角色1")
    ret = r.add(name="角色2", info="测试角色2")
    ret = r.add(name="角色3", info="测试角色3")

    rid = ret['data']['id']

    r.mod(rid, name='角色11', info='测试角色11111')

    rows = r.list()

    allids = ','.join([ x['id'] for x in rows['data']['data']])

    r.mod(allids, info='haha')

    rows = r.list()

    for row in rows['data']['data']:
        assert row['info'] == 'haha'

    one = rows['data']['data'][0]

    rows = r.list(name='角色2')
    assert len(rows['data']['data']) == 1

    ret = u.addperm(roleid=one['id'])
    roleid = ret['data'][0]['roleid']

    ret = u.q()
    rows = ret['data']['role'] 
    roledict =  set([ x['id'] for x in rows])

    assert roleid in roledict

    u.delperm(roleid=one['id'])
    ret = u.q()
    rows = ret['data']['role'] 
    roledict =  set([ x['id'] for x in rows])

    assert roleid not in roledict

    u.addperm(roleid=allids)
    ret = u.q()
    rows = ret['data']['role'] 
    roledict =  set([ x['id'] for x in rows])

    assert len(roledict) == allids.count(',')+1


def test_perm():
    global u

    u.login()
    u.q()

    r = Perm()
    r.clear()
    
    ret = r.add(name="perm_view", info="查看权限")
    ret = r.add(name="perm_mod", info="修改权限")
    ret = r.add(name="group_view", info="创建组")
    ret = r.add(name="group_mod", info="修改组")

    rid = ret['data']['id']

    r.mod(rid, name='xxx_view', info='测试权限11111')

    rows = r.list()

    allids = ','.join([ x['id'] for x in rows['data']['data']])

    r.mod(allids, info='haha')

    rows = r.list()

    for row in rows['data']['data']:
        assert row['info'] == 'haha'

    one = rows['data']['data'][0]

    rows = r.list(name='perm_mod')
    assert len(rows['data']['data']) == 1

    ret = u.addperm(permid=one['id'])
    permid = ret['data'][0]['permid']

    ret = u.q()
    rows = ret['data']['perm'] 
    permdict =  set([ x['id'] for x in rows])

    assert permid in permdict

    u.delperm(permid=one['id'])
    ret = u.q()
    rows = ret['data']['perm'] 
    permdict =  set([ x['id'] for x in rows])

    assert permid not in permdict


    ret = u.addperm(permid=allids)
    assert len(ret['data']) == allids.count(',')+1

    ret = u.q()
    assert len(ret['data']['perm']) == allids.count(',')+1

    ret = u.delperm(permid=allids)
    ret = u.q()
    assert len(ret['data']['perm']) == 0

def test_simple():
    global u
    
    #u.create()
    
    u.login()
    #u.q()
    #u.list()

    #r = Role()
    #ret = r.list()
    #roleid = ret['data']['data'][0]['id']
    #r.q(roleid)    

    #r.addperm(id=roleid, permid=6531811927155317021)
    #ret = r.q(roleid)    

    #rolepermid= ret['data']['perm'][-1]['id']
    #r.delperm(id=roleid, permid=6531811927155317021)

    #u2 = User('18800001111', 8888)
    #u2.clear()
    #u2.signup()
    #u2.list()

    #u.list()

    #g = Group()
    #ret = g.list()
    #g.q(ret['data']['data'][0]['id'])

    #u = User(appid='wx27edcac7e40b6688')
    #u.clear()
    #u.signup3rd('081Q3Ccx0qOOQc1rfNax0N6Hcx0Q3CcP')
    #u.login_reg_3rd('081okA9N1hTnv71OfhbN1x1A9N1okA93')

    pass


def main():
    name = ''
    if len(sys.argv) == 2:
        name = sys.argv[1]

    if not name:
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


