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
import config
from userbase import *

class Admin (BaseObjectHandler):
    dbname = config.DBNAME
    table = 'perms'

 
    
