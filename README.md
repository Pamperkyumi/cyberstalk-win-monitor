# CyberStalk Windows Monitor

**轻量级的「我现在在干什么」实时活动展示系统**

包含 Windows 客户端 + Flask 后端 + MySQL + Web 页面
支持扩展 iPhone / Apple Watch 数据上报

## ✨ 功能简介

### Windows 应用监控（核心）

- 获取当前前台窗口（进程名 + 标题）
- 获取所有有可见窗口的软件列表
- 定时上报到服务器

### Flask 后端

- 接收并存储客户端数据
- 提供 `/api/current` 接口给前端使用

### 网页展示

- iCloud 风格页面
- 实时显示"当前正在使用的应用"
- 显示"所有打开的软件"
- 当客户端离线时显示"距上次上报已过去 X 分钟"

### 可选扩展

- iPhone：锁定状态、电量、当前 App
- Apple Watch：心率数据

## 📦 安装与部署（快速）

### 1️⃣ 初始化数据库

```bash
mysql -u root -p < sql/schema.sql
```

会创建 `activity_db` 和需要的三张表。



### 2️⃣ 配置后端（server）

进入 `server/`：

```bash
cp config.example.py config.py
pip install -r requirements.txt
```



编辑 `config.py`：

```python
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "your_user",
    "password": "your_password",
    "database": "activity_db"
}
SECRET_TOKEN = "your_secret"
```



启动：

```
python server.py
```



访问前端页面：

```text
http://服务器IP:5000/
```



### 3️⃣ 配置 Windows 客户端

进入 `client_windows/`：

```bash
copy config.example.py config.py
pip install -r requirements.txt
```



修改配置：

```python
SERVER_URL = "http://服务器IP:5000/api/status"
SECRET_TOKEN = "与服务器一致"
REPORT_INTERVAL_SECONDS = 5
```



运行：

```bash
python monitor_apps.py
```



你就能在网页上看到实时活动了。

## 📱 可选扩展（简述）

项目已含接口：

| 功能        | 上传接口            | 查询接口                |
| :---------- | :------------------ | :---------------------- |
| 心率        | `/api/heartrate`    | `/api/latest_heartrate` |
| iPhone 状态 | `/api/phone_status` | `/api/phone_latest`     |

可通过 iPhone 快捷指令定时 POST JSON 即可使用。

## 📁 项目结构

```text
client_windows/   # Windows 客户端
server/           # Flask 服务 + 前端网页
sql/              # 数据库结构（schema.sql）
```

## 📜 LICENSE

MIT License – 可自由修改、使用、商用。