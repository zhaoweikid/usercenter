# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

import os
import sys
from webconfig import *

# 服务地址
HOST = '0.0.0.0'

# 服务端口
PORT = 6201

# 调试模式: True/False
# 生产环境必须为False
DEBUG = False

# 日志文件配置
#LOGFILE = os.path.join(HOME, 'log/usercenter.log')
LOGFILE = 'stdout'

# 数据库别名
DBNAME = 'usercenter'

# 数据库配置
DATABASE = {
    DBNAME: {
        'engine':'pymysql',
        'db': 'usercenter',
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'zhaowei',
        'passwd': '123456',
        'charset': 'utf8',
        'conn': 10,
    },
}

try:
    import dbconfig
    DATABASE.update(config.DATABASE)
except:
    pass

OPENUSER_ACCOUNT = {
    'wx27edcac7e40b6688':
    {
        'appid':'wx27edcac7e40b6688',
        'secret':'',
        'plat':'wxmicro',
    }
}

OPENSDK_SIGN_VAR = {
    'appid': 'X-Appid',
    'sign': 'X-Sign',
    'method': 'X-Method',
}




