# server.py
# -*- coding: utf-8 -*-
"""
CyberStalk 服务器端

功能：
- 接收 Windows 客户端上报的前台窗口与已打开程序列表 (/api/status)
- 提供最新状态给前端页面显示 (/api/current)
- 可选扩展：心率上传与查询 (/api/heartrate, /api/latest_heartrate, /api/heartrate_history)
- 可选扩展：手机状态上传与查询 (/api/phone_status, /api/phone_latest)
"""

from datetime import datetime
import json

from flask import Flask, request, jsonify, send_from_directory
import mysql.connector

# 从本地 config.py 读取数据库配置和 SECRET_TOKEN
# 仓库中只提供 config.example.py 作为示例
try:
    from config import DB_CONFIG, SECRET_TOKEN
except ImportError:
    raise RuntimeError(
        "未找到 config.py，请先复制 config.example.py 为 config.py 并填入实际配置。"
    )

app = Flask(__name__)


# -------------------- 工具函数 --------------------


def get_db_connection():
    """获取 MySQL 连接"""
    return mysql.connector.connect(**DB_CONFIG)


def check_token_from_request():
    """
    从请求中提取并验证 token。
    优先从 header: X-Auth-Token 读取，
    若没有，则尝试从 JSON body 中的 'token' 字段读取。
    """
    token = request.headers.get("X-Auth-Token")
    if not token:
        try:
            data = request.get_json(silent=True) or {}
        except Exception:
            data = {}
        token = data.get("token")

    if token != SECRET_TOKEN:
        return False
    return True


# -------------------- 静态页面 --------------------


@app.route("/")
def index_page():
    """返回前端页面"""
    return send_from_directory("static", "index.html")


# -------------------- Windows 状态上报 / 查询 --------------------


@app.route("/api/status", methods=["POST"])
def update_status():
    """
    接收本地 Windows 脚本上传的数据

    期望 JSON:
    {
      "token": "...",                # 或通过 Header: X-Auth-Token
      "active": {
        "process_name": "...",
        "window_title": "..."
      },
      "apps": [
        { "pid": 1234, "process_name": "...", "window_title": "..." },
        ...
      ]
    }
    """
    if not check_token_from_request():
        return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    active = data.get("active") or {}
    apps = data.get("apps") or []

    created_at = datetime.utcnow()
    active_process = active.get("process_name")
    active_title = active.get("window_title")
    apps_json = json.dumps(apps, ensure_ascii=False)

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO activity (created_at, active_process, active_title, apps_json)
            VALUES (%s, %s, %s, %s)
            """,
            (created_at, active_process, active_title, apps_json),
        )
        conn.commit()
    except Exception as e:
        print("DB insert activity error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return jsonify({"ok": True})


@app.route("/api/current", methods=["GET"])
def get_current():
    """
    返回最新一次上报的 Windows 状态。

    返回示例:
    {
      "timestamp": "2025-11-24 12:34:56",
      "active": {
        "process_name": "...",
        "window_title": "..."
      },
      "apps": [ ... ]
    }
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT created_at, active_process, active_title, apps_json
            FROM activity
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
    except Exception as e:
        print("DB select activity error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if not row:
        return jsonify({"status": "no data yet"})

    created_at, active_process, active_title, apps_json = row

    try:
        apps = json.loads(apps_json)
    except Exception:
        apps = []

    return jsonify(
        {
            "timestamp": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "active": {
                "process_name": active_process,
                "window_title": active_title,
            },
            "apps": apps,
        }
    )


# -------------------- 心率相关（可选扩展） --------------------


@app.route("/api/heartrate", methods=["POST"])
def heartrate():
    """
    接收心率上传（可选扩展）：
    期望 JSON:
      { "token": "...", "rate": 80, "source": "shortcut" }
    """
    if not check_token_from_request():
        return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    rate = data.get("rate")
    source = data.get("source", "shortcut")

    try:
        rate = int(rate)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid rate"}), 400

    created_at = datetime.utcnow()

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO heart_rate (created_at, rate, source) VALUES (%s, %s, %s)",
            (created_at, rate, source),
        )
        conn.commit()
    except Exception as e:
        print("DB insert heart_rate error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return jsonify({"status": "ok"})


@app.route("/api/latest_heartrate", methods=["GET"])
def latest_heartrate():
    """返回最近一次心率数据"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT created_at, rate
            FROM heart_rate
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
    except Exception as e:
        print("DB select latest heart_rate error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if not row:
        return jsonify({"status": "no data"})

    created_at, rate = row
    return jsonify(
        {
            "timestamp": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "rate": rate,
        }
    )


@app.route("/api/heartrate_history", methods=["GET"])
def heartrate_history():
    """返回最近 N 条心率数据，用于画图"""
    limit = 40
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT created_at, rate
            FROM heart_rate
            ORDER BY id DESC
            LIMIT {limit}
            """
        )
        rows = cursor.fetchall()
    except Exception as e:
        print("DB select heart_rate history error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if not rows:
        return jsonify({"points": []})

    rows = rows[::-1]  # 按时间正序

    points = []
    for created_at, rate in rows:
        points.append(
            {"timestamp": created_at.strftime("%Y-%m-%d %H:%M:%S"), "rate": rate}
        )

    return jsonify({"points": points})


# -------------------- 手机状态相关（可选扩展） --------------------


@app.route("/api/phone_status", methods=["POST"])
def phone_status():
    """
    接收 iPhone 使用状态（可选扩展）：
      locked = "是"/"否"
      battery = 0~100
      app = 前台应用名称
    """
    if not check_token_from_request():
        return jsonify({"error": "unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    print("DEBUG /api/phone_status:", data)

    locked = data.get("locked")
    battery = data.get("battery")
    appname = data.get("app")
    source = data.get("source", "iphone")

    created_at = datetime.utcnow()

    try:
        battery = int(battery)
    except Exception:
        battery = None

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO phone_status (created_at, locked, battery, app, source)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (created_at, locked, battery, appname, source),
        )
        conn.commit()
    except Exception as e:
        print("DB insert phone_status error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    return jsonify({"status": "ok"})


@app.route("/api/phone_latest", methods=["GET"])
def phone_latest():
    """返回最近一次手机使用状态"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT created_at, locked, battery, app
            FROM phone_status
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
    except Exception as e:
        print("DB select phone_latest error:", e)
        return jsonify({"error": "db error"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    if not row:
        return jsonify({"status": "no data"})

    created_at, locked, battery, appname = row
    return jsonify(
        {
            "timestamp": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "locked": locked,
            "battery": battery,
            "app": appname,
        }
    )


# -------------------- 入口 --------------------


if __name__ == "__main__":
    # 开源示例中保留 0.0.0.0 方便本地/局域网访问
    # 若只在本机调试，可改为 127.0.0.1
    app.run(host="0.0.0.0", port=5000)
