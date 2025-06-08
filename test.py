import subprocess
import os

# Electron 应用路径
app_path = '/Users/apple/PycharmProjects/MousePupilAI/web/out/web-darwin-arm64/web.app'

# 用 open 命令启动 .app
proc = subprocess.Popen(['open', app_path])
proc.wait()