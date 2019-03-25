# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

urls = (
    ('/v1/user/ping', "usercenter.Ping"),
    # 用户管理
    ('^/v1/user/(login|logout|q|list|signup|mod|addgroup|delgroup|addperm|delperm)$', "usercenter.User"),
    # 用户组管理
    ('^/v1/group/(add|del|mod|q|list)$', "groups.Group"),
    # 权限管理
    ('^/v1/perm/(add|del|mod|q|list)$', "perms.Perm"),
    # 角色管理
    ('^/v1/role/(add|del|mod|q|list)$', "perms.Role"),
    # 管理员功能
    ('^/v1/admin/(userlist)$', "admin.Admin"),

)
