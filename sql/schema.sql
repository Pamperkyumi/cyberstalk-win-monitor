/*
===========================================================
 CyberStalk 数据库初始化脚本
===========================================================

本脚本包含 3 张表：

  1) activity       - Windows 客户端的应用监控数据
  2) heart_rate     - （可选扩展）心率数据（Apple Watch / 健康 App）
  3) phone_status   - （可选扩展）iPhone 手机使用状态数据

使用方法：
    mysql -u root -p < schema.sql
    或者手动在 MySQL 客户端执行本文件内容。

===========================================================
*/

/* --------------------------------------------------------
   创建数据库（如果不存在）
-------------------------------------------------------- */
CREATE DATABASE IF NOT EXISTS activity_db
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE activity_db;


/* --------------------------------------------------------
   1. Windows 应用监控表
      - 存储当前活动窗口和所有打开的软件列表
-------------------------------------------------------- */
DROP TABLE IF EXISTS activity;

CREATE TABLE activity (
    id INT AUTO_INCREMENT PRIMARY KEY,

    /* 数据上报时间（UTC） */
    created_at DATETIME NOT NULL,

    /* 当前活动窗口（前台窗口） */
    active_process VARCHAR(256) DEFAULT NULL,
    active_title   TEXT          DEFAULT NULL,

    /* 所有打开的软件列表（JSON 字符串） */
    apps_json      LONGTEXT      NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


/* --------------------------------------------------------
   2. 心率表（可选扩展）
      - 由 iPhone Shortcut 上报 Apple Watch 的心率
      - 如用户不启用心率功能，此表不会被写入数据
-------------------------------------------------------- */
DROP TABLE IF EXISTS heart_rate;

CREATE TABLE heart_rate (
    id INT AUTO_INCREMENT PRIMARY KEY,

    /* 上报时间（UTC） */
    created_at DATETIME NOT NULL,

    /* 心率值（整数） */
    rate INT NOT NULL,

    /* 数据来源：如 shortcut / watch / other */
    source VARCHAR(32) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


/* --------------------------------------------------------
   3. 手机状态表（可选扩展）
      - 用于记录 iPhone 的状态：
          locked: 是否锁屏 ("是" / "否")
          battery: 电池百分比
          app: 前台应用名称
-------------------------------------------------------- */
DROP TABLE IF EXISTS phone_status;

CREATE TABLE phone_status (
    id INT AUTO_INCREMENT PRIMARY KEY,

    /* 上报时间（UTC） */
    created_at DATETIME NOT NULL,

    /* 是否锁屏：是 / 否  */
    locked VARCHAR(8) DEFAULT NULL,

    /* 电池百分比（0~100） */
    battery INT DEFAULT NULL,

    /* 当前前台应用名称 */
    app VARCHAR(256) DEFAULT NULL,

    /* 上报来源（一般为 iphone） */
    source VARCHAR(32) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


/*
===========================================================
  初始化完成！
===========================================================

你现在可以：

  1. 在 server/config.py 中配置 DB_CONFIG
  2. 运行 Flask 服务器
  3. 运行 Windows 客户端 monitor_apps.py
  4. （可选）在 iPhone 快捷指令中调用心率 / phone_status 接口

===========================================================
*/
