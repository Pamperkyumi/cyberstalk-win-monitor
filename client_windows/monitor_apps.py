# monitor_apps.py
# -*- coding: utf-8 -*-
"""
CyberStalk Windows 客户端

功能：
- 获取当前前台活动窗口信息（应用名 + 窗口标题）
- 枚举当前所有有可见窗口的进程（排除部分系统/后台进程）
- 周期性将这些数据以 JSON 形式上报到服务器

依赖：
- psutil
- pywin32 (win32gui, win32process)
- requests

配置：
- 请在同目录下创建 config.py（从 config.example.py 复制），
  并设置 SERVER_URL、SECRET_TOKEN、REPORT_INTERVAL_SECONDS 等。
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import psutil
import win32gui
import win32process
import requests

try:
    # config.py 为本地配置文件，开源仓库只提供 config.example.py
    from config import SERVER_URL, SECRET_TOKEN, REPORT_INTERVAL_SECONDS
except ImportError:
    raise RuntimeError(
        "未找到 config.py，请先复制 config.example.py 为 config.py 并填写实际配置。"
    )


def get_active_window_info() -> Optional[Dict[str, Any]]:
    """
    获取当前前台活动窗口的信息：
    - 窗口标题
    - 进程 ID
    - 进程名（程序名）

    返回:
        dict 或 None，例如:
        {
            "hwnd": 123456,
            "window_title": "Visual Studio Code",
            "process_name": "monitor_apps.py",
            "pid": 4321
        }
    """
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None

    title = win32gui.GetWindowText(hwnd)
    tid, pid = win32process.GetWindowThreadProcessId(hwnd)

    try:
        p = psutil.Process(pid)
        proc_name = p.name()
    except psutil.NoSuchProcess:
        proc_name = "Unknown"
    except psutil.AccessDenied:
        proc_name = "AccessDenied"

    return {
        "hwnd": hwnd,
        "window_title": title,
        "process_name": proc_name,
        "pid": pid,
    }


def get_open_apps() -> List[Dict[str, Any]]:
    """
    获取当前“有可见窗口”的软件列表（排除大量后台/系统进程）

    返回:
        列表，每项形如:
        {
            "pid": 1234,
            "process_name": "chrome.exe",
            "window_title": "Bilibili - Google Chrome"
        }
    """
    apps_by_pid: Dict[int, Dict[str, Any]] = {}

    def enum_window_callback(hwnd, extra):
        # 只要可见窗口
        if not win32gui.IsWindowVisible(hwnd):
            return

        title = win32gui.GetWindowText(hwnd)
        if not title.strip():
            return

        # 过滤太小或不可交互的窗口
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        if width < 100 or height < 50:
            return

        # 获取进程信息
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            p = psutil.Process(pid)
            proc_name = p.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            proc_name = "Unknown"

        # 粗略过滤一些典型系统/后台程序
        system_like = {
            "svchost.exe",
            "System Idle Process",
            "System",
            "SearchApp.exe",
            "RuntimeBroker.exe",
        }
        if proc_name in system_like:
            return

        # 同一 PID 可能有多个窗口：保留标题更长的那个
        if pid not in apps_by_pid:
            apps_by_pid[pid] = {
                "pid": pid,
                "process_name": proc_name,
                "window_title": title,
            }
        else:
            if len(title) > len(apps_by_pid[pid]["window_title"]):
                apps_by_pid[pid]["window_title"] = title

    # 枚举所有顶层窗口
    win32gui.EnumWindows(enum_window_callback, None)

    apps = list(apps_by_pid.values())
    apps.sort(key=lambda x: x["process_name"].lower())
    return apps


def main_loop(interval_seconds: int = None) -> None:
    """
    主循环：
    - 每隔 interval_seconds 秒收集一次数据
    - POST 到 SERVER_URL
    """
    if interval_seconds is None:
        interval_seconds = REPORT_INTERVAL_SECONDS

    print(f"启动本地应用监控，上报间隔：{interval_seconds} 秒")
    print(f"上报地址：{SERVER_URL}")

    try:
        while True:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            active = get_active_window_info()
            apps = get_open_apps()

            payload = {
                "timestamp": now_str,
                "active": active,
                "apps": apps,
            }

            try:
                resp = requests.post(
                    SERVER_URL,
                    json=payload,
                    headers={"X-Auth-Token": SECRET_TOKEN},
                    timeout=5,
                )
                print(f"[{now_str}] 上传状态：", resp.status_code, resp.text)
            except Exception as e:
                print(f"[{now_str}] 上传失败：", e)

            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("收到中断信号，退出。")


if __name__ == "__main__":
    # 如果想临时修改间隔，可以改这里的参数
    main_loop()
