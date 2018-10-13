# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

import usercenter

urls = (
    ('/v1/user/ping', "usercenter.Ping"),
    # select, update
    ('^/v1/user/([a-zA-Z0-9_]+)$', "usercenter.User"),
    # select/create
    ('^/v1/user$', "usercenter.User"),
)
