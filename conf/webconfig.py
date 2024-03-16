# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

import os
import sys
HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# URLS配置
URLS = None

# 静态路径配置
STATICS = {'/admin/': '/'}

# 模板配置
TEMPLATE = {
    'cache': True,
    'path': 'templates',
    'tmp': os.path.join(HOME, 'tmp'),
}

# APP就是一个子目录
APPS = (

)

# 中间件
MIDDLEWARE = (
    # middleware
    'SessionMiddleware',
    #'SignMiddleware',
)

# 中间件配置
MIDDLEWARE_CONF = {
    'SignMiddleware': {
        'apps':{  # appid: {userid:xx, secret:xx}
        },
    },
    'SessionMiddleware': {
    }
}

# WEB根路径
DOCUMENT_ROOT = os.path.join(os.path.dirname(HOME), 'usercenter_admin')

# 页面编码
CHARSET = 'UTF-8'

# session配置
# 1. session存储在文件中，expire为过期时间（秒），path为存储路径
# {'store':'SessionFile',  'expire':30, 'config':{'path':'/tmp'}}
# 2. session存储在redis中，expire为过期时间（秒），addr为redis的地址
# {'store':'SessionRedis', 'expire':30, 'server':{'host':'127.0.0.1', 'port':6379, 'db':0}}
SESSION = {
    'store':'SessionRedis',
    'expire':3600,
    'cookie_name': 'sid',
    'config':{
        'redis_conf': {
            'host':'127.0.0.1',
            'port':6379,
            'db':0,
        },
        'user_key':'userid',
    },
    'enable':True
}
