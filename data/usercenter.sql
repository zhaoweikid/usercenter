DROP DATABASE usercenter;
CREATE DATABASE usercenter CHARSET utf8 COLLATE utf8_general_ci;
USE usercenter;
SET NAMES utf8;

CREATE TABLE IF NOT EXISTS users (
	id bigint not null primary key,
	username varchar(128) not null unique,
	password varchar(64) not null,
    email varchar(128) unique,
	mobile varchar(18) unique,
	head varchar(128) not null default '', -- head url or path
	score int(11) not null default 0, -- 积分
	stage int(11) not null default 1, -- 等级
	ctime unsigned int(11), -- 创建时间
	uptime unsigned int(11), -- 更新时间
	logtime unsigned int(11), -- 最后一次登陆时间
	regip char(128) not null default '',
	status tinyint default 0, -- 1未验证 2正常 3封禁 4删除
	extend varchar(8192),
	key (username, email, mobile)
);
insert into users(id,username,password,ctime,status) values (1,'admin','usercenter+admin',now(),2);

-- 权限表
CREATE TABLE IF NOT EXISTS power (
	id int(11) not null primary key auto_increment,
    name varchar(128) not null unique,
    memo varchar(128)  
);
insert into power(id,name,memo) values (1,'sysadmin','系统管理');
insert into power(id,name,memo) values (1,'default','普通用户');

-- 组
CREATE TABLE IF NOT EXISTS groups (
	id int(11) not null primary key auto_increment,
	name varchar(128) not null unique,
	ownerid int(11) not null, -- 拥有人
	power varchar(4096) not null, -- 组权限
	ctime datetime,
	uptime datetime,
	key (name)
); 
insert into groups(id,name,ownerid,power,ctime,uptime) values (1,'admin',1,1,now(),now());

-- 用户组关系
CREATE TABLE IF NOT EXISTS usergroup (
	id int(11) not null primary key auto_increment,
	userid int(11) not null,
	groupid int(11) not null,
	ctime datetime
);
insert into usergroup(id,userid,groupid,ctime) values (1,1,1,now());

-- 用户日志
CREATE TABLE IF NOT EXISTS userlog (
	id int(11) not null primary key auto_increment,
	userid int(11) not null,
	opuserid int(11) not null, -- 执行动作的用户
	action varchar(32) not null, -- login,logout,reg,modify,...
	content varchar(4096),
	ctime datetime
);

-- 基本设置
CREATE TABLE IF NOT EXISTS setting (
	id int(11) not null primary key auto_increment,
	user_new_status tinyint not null default 2
);
insert into setting set user_new_status=2;


