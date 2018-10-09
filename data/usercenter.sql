DROP DATABASE usercenter;
CREATE DATABASE usercenter CHARSET utf8 COLLATE utf8_general_ci;
USE usercenter;
SET NAMES utf8;

DROP TABLE users;
CREATE TABLE IF NOT EXISTS users (
	id bigint not null primary key,
	username varchar(128) not null unique,
	password varchar(64) not null,
    email varchar(128) unique,
	mobile varchar(18) unique,
	head varchar(128) not null default '', -- head url or path
	score int(11) not null default 0, -- 积分
	stage int(11) not null default 1, -- 等级
	ctime int(11) unsigned, -- 创建时间
	uptime int(11) unsigned, -- 更新时间
	logtime int(11) unsigned, -- 最后一次登陆时间
	regip varchar(128) not null default '',
	status tinyint default 0, -- 1未验证 2正常 3封禁 4删除
	isadmin tinyint default 0, -- 1admin 0user
	extend varchar(8192),
	key (username, email, mobile)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
insert into users(id,username,password,ctime,status,isadmin) values (1,'admin','',UNIX_TIMESTAMP(now()),2,1);

-- 基本设置
DROP TABLE settings;
CREATE TABLE IF NOT EXISTS settings (
	id bigint(20) not null primary key,
	userid bigint(20) not null,
	name varchar(128) not null,
	value varchar(512) not null,
	key (userid),
	key (name)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- 权限表
DROP TABLE perm;
CREATE TABLE IF NOT EXISTS perm (
	id bigint(20) not null primary key,
    name varchar(128) not null unique,
    memo varchar(128)  
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
insert into perm(id,name,memo) values (1,'sysadmin','系统管理');
insert into perm(id,name,memo) values (2,'default','普通用户');

-- 组
DROP TABLE groups;
CREATE TABLE IF NOT EXISTS groups (
	id bigint(20) not null primary key,
	name varchar(128) not null unique,
	userid bigint(20) not null, -- 拥有人
	perm varchar(4096) not null, -- 组权限
	ctime int(11) unsigned,
	uptime int(11) unsigned
)ENGINE=InnoDB DEFAULT CHARSET=utf8; 

insert into groups(id,name,userid,perm,ctime,uptime) values (1,'admin',1,1,UNIX_TIMESTAMP(now()),UNIX_TIMESTAMP(now()));

-- 用户组关系 user<=>group
DROP TABLE usergroup;
CREATE TABLE IF NOT EXISTS usergroup (
	id bigint(20) not null primary key,
	userid bigint(20) not null,
	groupid bigint(20) not null,
	ctime int(11) unsigned
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
insert into usergroup(id,userid,groupid,ctime) values (1,1,1,UNIX_TIMESTAMP(now()));


