# coding: utf-8
import os, sys
import json
import urllib, urllib2

class MyRequest (urllib2.Request):
    method = 'GET'
    def get_method(self):
        return self.method

cookie = ''

def request(url, method, values=None):
    global cookie
    print '\33[0;33m' + '='*30 + '\33[0m'
    print '>>>>', 
    print method, url
    print 'values:', values
  
    data = None
    if values:
        data = urllib.urlencode(values)
    headers = {
        'User-Agent': 'testclient',
        #'Cookie': 'sid=%d'
    }
    if cookie:
        headers['Cookie'] = cookie
    #req = MyRequest(url, data, headers)
    req = MyRequest(url, data, headers=headers)
    req.method = method
    print '<<<<', 

    ret = {}
    try:
        resp = urllib2.urlopen(req)
    except Exception, e:
        print e.code
        print e    
    else:
        print resp.code
        #print resp.headers
        
        c = resp.headers.get('Set-Cookie')
        if c:
            cookie = c.split(';')[0]

        s = resp.read()
        print s
        ret = json.loads(s)

    return ret



def main():
    prefix_url = 'http://127.0.0.1:6200/v1'
    xid = 12


    url = 'http://127.0.0.1:6200/v1/user?mobile=13800000%03d&password=123456&username=zhaowei%d&email=zhaowei%d@qq.com' % (xid, xid, xid)
    request(url, 'POST')

    url = prefix_url + '/user/login?password=123456&username=zhaowei%d@qq.com' % (xid)
    obj = request(url, 'GET')

    url = prefix_url + '/user/%d' % (obj['data']['uid'])
    request(url, 'GET')
    
    url = prefix_url + '/user'
    request(url, 'GET')

    url = prefix_url + '/user?status=2'
    request(url, 'PUT')

    url = prefix_url + '/user/%d' % (obj['data']['uid'])
    request(url, 'GET')
 


if __name__ == '__main__':
    main()

