# coding: utf-8
import os, sys
import json
import urllib
import urllib.request
import pprint

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

        s = resp.read()
        print(s)
        ret = json.loads(s)
        pprint.pprint(ret)

    return ret



def main():
    prefix_url = 'http://127.0.0.1:6300/v1'
    xid = 13

    url = prefix_url + '/user/signup?mobile=13800000%03d&password=123456&username=zhaowei%d&email=zhaowei%d@qq.com' % (xid, xid, xid)
    #request(url, 'POST')

    url = prefix_url + '/user/login?password=123456&username=zhaowei%d' % (xid)
    obj = request(url, 'GET')

    url = prefix_url + '/user/q?id=%d' % (int(obj['data']['userid']))
    request(url, 'GET')
    
    url = prefix_url + '/user/list'
    request(url, 'GET')

    url = prefix_url + '/user/mod?status=2'
    request(url, 'POST')

    url = prefix_url + '/user/q?id=%d' % (int(obj['data']['userid']))
    request(url, 'GET')
 

def group():
    prefix_url = 'http://127.0.0.1:6300/v1'
    xid = 13

    url = prefix_url + '/user/login?password=123456&username=zhaowei%d' % (xid)
    obj = request(url, 'GET')

    userid = obj['data']['userid']

    url = prefix_url + '/user/q?id=%d' % (int(obj['data']['userid']))
    request(url, 'GET')
 
    url = prefix_url + '/perm/list'
    obj = request(url, 'GET')

    url = prefix_url + '/perm/q?id=%s' % (obj['data']['data'][-1]['id'])
    obj = request(url, 'GET')

    #url = prefix_url + '/perm/add?name=test_view&info=%s' % (urllib.parse.quote('测试查看'))
    #obj = request(url, 'POST')

    permid = obj['data']['id']
    url = prefix_url + '/perm/mod?id=%s&info=testview2' % (permid)
    obj = request(url, 'POST')

    url = prefix_url + '/perm/list'
    obj = request(url, 'GET')

    #url = prefix_url + '/perm/del?id=%s' % (permid)
    #obj = request(url, 'POST')
    #url = prefix_url + '/perm/list'
    #obj = request(url, 'GET')
    
    url = prefix_url + '/role/add?name=%s&info=test1'  % ('role1')
    obj = request(url, 'POST')

    url = prefix_url + '/role/list'
    obj = request(url, 'GET')

    url = prefix_url + '/user/addperm?roleid=6515860480953707676' 
    obj = request(url, 'POST')

    url = prefix_url + '/user/q'
    request(url, 'GET')




if __name__ == '__main__':
    #main()
    group()


