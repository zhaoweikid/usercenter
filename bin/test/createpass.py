# coding:utf-8
import os, sys
import random
import hashlib


def create_password(passwd, salt=None):
    if salt is None:
        salt = random.randint(1, 1000000)
    saltstr = '%06d' % salt
    tmp = passwd+saltstr
    return 'sha1$%s$%s' % (salt, hashlib.sha1(tmp.encode('utf-8')).hexdigest())


if __name__ == '__main__':
    print(create_password(sys.argv[1]))

