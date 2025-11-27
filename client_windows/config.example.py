# config.example.py
# ----------------------------------------
# 使用说明：
# 1. 将本文件复制为 config.py
# 2. 在 config.py 中填写实际的服务器地址和 SECRET_TOKEN
# 3. 建议在 .gitignore 中忽略 config.py，避免泄露敏感信息
# ----------------------------------------

# 服务器地址：
# - 如果你直接让客户端访问 Flask 的 5000 端口，可以用：
#   SERVER_URL = "http://YOUR_SERVER_IP:5000/api/status"
# - 如果你前面有 Nginx + HTTPS，则可以用：
#   SERVER_URL = "https://your-domain.com/api/status"
SERVER_URL = "http://YOUR_SERVER_IP:5000/api/status"

# 必须和服务器端 config.py 中的 SECRET_TOKEN 保持一致
SECRET_TOKEN = "CHANGE_ME_TO_SAME_SECRET_AS_SERVER"

# 上报间隔（秒）
REPORT_INTERVAL_SECONDS = 5
