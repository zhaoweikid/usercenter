# coding:utf-8
import os, sys
import json
import logging 

log = logging.getLogger()


def perm_verify(ses, perms):
    # 超级管理员
    if ses.get('isadmin', 0):
        return True

    # 普通用户检查权限
    p = ses.get('allperm')
    if not p:
        return False

    allperms = set(p)
    s = set(perms) 
    if not s.issubset(allperms):
        return False
    else:
        return True
    


# 检查权限
def check_perm(perms):
    def f(func):
        def _(self, *args, **kwargs):
            # 超级管理员
            if self.ses.get('isadmin', 0):
                return func(self, *args, **kwargs)

            # 普通用户检查权限
            p = self.ses.get('allperm')
            if not p:
                return self.fail(ERR_PERM)
            allperms = set(p)
            s = set(perms) 
            if not s.issubset(allperms):
                self.fail(ERR_PERM)
                return
            return func(self, *args, **kwargs)
        return _
    return f

# 检查是否管理员
def check_admin(func):
    def _(self, *args, **kwargs):
        if not self.ses['isadmin']:
            self.fail(ERR_PERM)
            return
        return func(self, *args, **kwargs)
    return _




