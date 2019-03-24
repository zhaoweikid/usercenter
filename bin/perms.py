# coding: utf-8
import os, sys
import json, random, hashlib
import time
import copy
from zbase3.web import core
from zbase3.web.validator import *
from zbase3.base.dbpool import get_connection
from zbase3.utils import createid
import logging
from userbase import *

class Perm (BaseObjectHandler):
    dbname = 'usercenter'
    table = 'perms'

 
class Role (BaseObjectHandler):
    dbname = 'usercenter'
    table = 'roles'


