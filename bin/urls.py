# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

urls = (
    ('^/uc/v1/ping', "usercenter.Ping"),
    # 用户管理
    ('^/uc/v1/user/(login|login3rd|login_reg_3rd|logout|q|list|signup|signup3rd|mod|addgroup|delgroup|addperm|delperm|get_user)$', "usercenter.User"),
    # 用户组管理
    ('^/uc/v1/group/(add|del|mod|q|list)$', "groups.Group"),
    # 权限管理
    ('^/uc/v1/perm/(add|del|mod|q|list)$', "perms.Perm"),
    # 角色管理
    ('^/uc/v1/role/(add|del|mod|q|list|addperm|delperm)$', "perms.Role"),
    # 管理员功能
    ('^/uc/v1/admin/(userlist)$', "admin.Admin"),

)
