# vim: set ts=4 et sw=4 sts=4 fileencoding=utf-8 :

urls = (
    ('^/uc/v1/ping', "usercenter.Ping"),
    # 用户管理
    ('^/uc/v1/user(?:/([0-9]+))?$', "usercenter.User"),
    ('^/uc/v1/user/(query|modify|signin|signin_3rd|signout|signup|signup_3rd|group_join|group_quit|perm_give|perm_take)$', 
            "usercenter.User"),
    # 用户组管理
    ('^/uc/v1/group/(create|modify|query|delete)?$', "groups.Group"),
    # 权限管理
    ('^/uc/v1/perm/(create|modify|query|delete)?$', "perms.Perm"),
    # 角色管理
    ('^/uc/v1/role/(create|modify|query|delete|perm_give|perm_take)$', "perms.Role"),
    # 管理员功能
    ('^/uc/v1/admin/(userlist)$', "admin.Admin"),

)
