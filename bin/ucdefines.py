# coding: utf-8
from zbase3.web import advance
OK  = 0
ERR = -1
ERR_USER    = -2
ERR_PARAM   = -3
ERR_AUTH    = -4
ERR_ACTION  = -5
ERR_DATA    = -6
ERR_PERM    = -7
ERR_INTERNAL= -8
ERR_SIGN    = -9

errstr = {
    OK: '成功',
    ERR: '失败',
    ERR_USER: '用户错误',
    ERR_PARAM: '参数错误',
    ERR_AUTH: '认证失败',
    ERR_ACTION: '操作失败',
    ERR_DATA: '数据错误',
    ERR_PERM: '权限错误',
    ERR_INTERNAL: '内部错误',
    ERR_SIGN: '签名错误',
}

advance.errmsg.update(errstr)


# 未认证
STATUS_NOAUTH = 1
# 正常
STATUS_OK  = 2
# 封禁
STATUS_BAN = 3
# 删除
STATUS_DEL = 4


