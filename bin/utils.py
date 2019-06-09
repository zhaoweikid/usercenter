# coding:utf-8
import os, sys
import requests
import json
import logging 
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


def test():
    ret = get_openid(sys.argv[1], 'wx27edcac7e40b6688')
    print(ret)
    
if __name__ == '__main__':
    test()

