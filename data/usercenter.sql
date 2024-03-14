-- DROP DATABASE usercenter;
CREATE DATABASE usercenter CHARSET utf8 COLLATE utf8_general_ci;
USE usercenter;
SET NAMES utf8mb4;

-- 用户表
DROP TABLE users;
CREATE TABLE IF NOT EXISTS users (
	id bigint not null primary key AUTO_INCREMENT,
	username varchar(128) not null unique COMMENT '用户名',
	password varchar(64) not null COMMENT '密码',
	usertype tinyint default 1 COMMENT '用户类型 1.基础用户 2.开放平台用户',
    email varchar(128) unique COMMENT '邮件地址',
	mobile varchar(18) unique COMMENT '手机号',
	head varchar(128) not null default '' COMMENT '头像url',
	score int(11) not null default 0 COMMENT '积分',
	stage int(11) not null default 1 COMMENT '等级',
	ctime datetime COMMENT '创建时间',
	utime datetime COMMENT '更新时间',
	logtime datetime COMMENT '最后一次登录时间',
	regip varchar(128) not null default '' COMMENT '注册ip',
	status tinyint default 1 COMMENT '状态: 1.注册未验证 2.正常 3.封禁 4.删除',
	isadmin tinyint default 0 COMMENT '是否为超级管理员 1是 0否',
	extend varchar(8192) COMMENT '扩展字段，存储json数据',
	key (username, email, mobile)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

insert into users(id,username,password,ctime,status,isadmin) values (1,'admin','sha1$123456$71dd07494c5ee54992a27746d547e25dee01bd97',now(),2,1);

-- 开放平台账号
DROP TABLE apps;
CREATE TABLE IF NOT EXISTS apps (
	id bigint(20) not null primary key AUTO_INCREMENT,
	userid bigint(20) not null,
	appid varchar(128) not null unique COMMENT '开放平台账号',
	pubkey varchar(1024) COMMENT '公钥',
	prikey varchar(4096) COMMENT '私钥',
	secret varchar(256) not null COMMENT '开放平台签名密钥',
	status tinyint default 1 COMMENT '状态: 1.正常 2.停用',
	method varchar(64) not null default 'md5' COMMENT '验证方法 md5/sha256/rsa',
	ctime datetime COMMENT '创建时间',
	utime datetime COMMENT '更新时间'
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 第三方系统账号, 用于授权登录
DROP TABLE open_account;
CREATE TABLE IF NOT EXISTS open_account (
	id bigint(20) not null primary key AUTO_INCREMENT,
	plat varchar(128) not null COMMENT '第三方系统名称，如：wx/wxm/alipay/qq/taobao',
	appid varchar(256) not null COMMENT '第三方系统账号',
	secret varchar(128) not null COMMENT '签名字符串',	
	pubkey varchar(1024) COMMENT '公钥',
	prikey varchar(4096) COMMENT '私钥',
	status tinyint default 1 COMMENT '状态: 1.正常 2.停用',
	ctime datetime,
	utime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; 

-- 第三方系统授权登录后，记录的用户信息
DROP TABLE open_user;
CREATE TABLE IF NOT EXISTS open_user (
	id bigint(20) not null primary key AUTO_INCREMENT,
	userid bigint(20) not null,
	appid varchar(128) not null default '' COMMENT '第三方系统账号',
	openid varchar(128) not null default '' COMMENT '第三方系统识别的用户id',
	ctime datetime,
	utime datetime,
	key (appid, openid)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; 

-- 用户组，同时表示了组织关系
DROP TABLE groups;
CREATE TABLE IF NOT EXISTS groups (
	id bigint(20) not null primary key AUTO_INCREMENT,
	parentid bigint(20) not null COMMENT '上级组',
	name varchar(128) not null unique COMMENT '组名',
    info varchar(128) COMMENT '组描述',
	ctime datetime,
	utime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; 

-- 用户和组的关系
DROP TABLE user_group;
CREATE TABLE IF NOT EXISTS user_group (
	id bigint(20) not null primary key AUTO_INCREMENT,
	userid bigint(20) not null,
	groupid bigint(20) not null,
	ctime datetime,
	utime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

insert into user_group(id,userid,groupid,ctime) values (1,1,1,now());



-- 基本设置。比如针对密码的要求
DROP TABLE settings;
CREATE TABLE IF NOT EXISTS settings (
	id bigint(20) not null primary key AUTO_INCREMENT,
	name varchar(128) not null COMMENT '设置项名称',
	value varchar(512) not null COMMENT '设置项的值',
	ctime datetime,
	utime datetime,
	key (name)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 设置密码强度: 1.任意8字符 2.包含数字和英文的8字符 3.包含数字和英文小写、英文大写的8字符 4.包含数字、英文大写、英文小写、其他符号的8字符
insert into settings(id,name,value,ctime,utime) values (1, 'pwd_strength', '2', now(), now());
-- 密码过期时间, 单位天，为0表示永不过期
insert into settings(id,name,value,ctime,utime) values (2, 'pwd_expire', '0', now(), now());
-- 10分钟内最大密码错误次数，超过次数后会被锁定
insert into settings(id,name,value,ctime,utime) values (3, 'pwd_err_count', '3', now(), now());
-- 密码错误后的锁定时间，单位分钟
insert into settings(id,name,value,ctime,utime) values (4, 'pwd_lock_time', '10', now(), now());

-- 用户登录记录
DROP TABLE `login_record`;
CREATE TABLE IF NOT EXISTS `login_record` (
	id bigint(20) not null primary key AUTO_INCREMENT,
	userid bigint(20) not null,
	ip varchar(256) not null COMMENT '登录ip',
	action varchar(128) not null COMMENT '操作，目前可以为 login/logout',
	state smallint not null default 1 COMMENT '登录结果，1.成功 0.失败',
	memo varchar(512) COMMENT '其他信息',
	ctime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 权限表
DROP TABLE `perms`;
CREATE TABLE IF NOT EXISTS `perms` (
	id bigint(20) not null primary key AUTO_INCREMENT,
    name varchar(128) not null unique COMMENT '权限名称',
    info varchar(128) COMMENT '权限描述',
	ctime datetime,
	utime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

insert into perms(id,name,info) values (1,'perm_view','权限查看');
insert into perms(id,name,info) values (2,'perm_mod','权限增加修改');

-- 角色表，角色是权限的集合
DROP TABLE `roles`;
CREATE TABLE IF NOT EXISTS `roles` (
	id bigint(20) not null primary key AUTO_INCREMENT,
    name varchar(128) not null unique COMMENT '角色名称',
    info varchar(128) COMMENT '角色描述',
	ctime datetime,
	utime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

insert into roles(id,name,info,ctime,utime) values (1,'admin', '系统管理员', now(), now());

-- 角色和权限的对应关系表
DROP TABLE `role_perm`;
CREATE TABLE IF NOT EXISTS `role_perm` (
	id bigint(20) not null primary key AUTO_INCREMENT,
	permid bigint(20) not null,
	roleid bigint(20) not null,
	ctime datetime,
	utime datetime,
	UNIQUE KEY `rp_uniq_id` (`permid`, `roleid`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户和权限、角色的关系表
-- 用户既可以对应角色，也可以对应权限。实际处理会拿到角色对应的所有权限，和直接分配的权限合并在一起
DROP TABLE user_perm;
CREATE TABLE IF NOT EXISTS user_perm (
	id bigint(20) not null primary key AUTO_INCREMENT,
	userid bigint(20) not null,
	permid bigint(20) not null default 0 COMMENT '权限id，为0表示无权限',
	roleid bigint(20) not null default 0 COMMENT '角色id，为0表示无角色',
	ctime datetime,
	utime datetime
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



