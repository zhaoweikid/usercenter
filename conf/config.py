# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

import os
import sys
from webconfig import *

# 服务地址
HOST = '0.0.0.0'

# 服务端口
PORT = 6101

# 调试模式: True/False
# 生产环境必须为False
DEBUG = False

# 日志文件配置
LOGFILE = os.path.join(HOME, '../log/usercenter.log')

# 数据库配置
DATABASE = {
    'usercenter': {
        'engine':'pymysql',
        'db': 'elec_usercenter',
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'passwd': 'KORpVLvYHiIOmrD4',
        'charset': 'utf8',
        'conn': 10,
    },
}

OPENUSER_ACCOUNT = {
    'wx27edcac7e40b6688':
        {
        'appid':'wx27edcac7e40b6688',
        'secret':'475c663232ab60adf2f9882eb4bf3b3b',
        'plat':'wxmicro',
        }
}

