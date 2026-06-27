#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/mysql_web_console"
PID_FILE="$APP_DIR/.uvicorn.pid"
HOST="0.0.0.0"
PORT=8000

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "服务已在运行中 (PID: $OLD_PID)"
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# 检测 MySQL 是否可达，不可达则尝试通过 brew services 启动
if ! mysqladmin ping --silent 2>/dev/null; then
    echo "MySQL 未运行，尝试启动..."
    if command -v brew &>/dev/null; then
        brew services start mysql
        echo "等待 MySQL 就绪..."
        for i in $(seq 1 30); do
            if mysqladmin ping --silent 2>/dev/null; then
                echo "MySQL 已启动"
                break
            fi
            if [ "$i" -eq 30 ]; then
                echo "MySQL 启动超时，请手动检查"
                exit 1
            fi
            sleep 1
        done
    else
        echo "未找到 brew，请手动启动 MySQL 后重试"
        exit 1
    fi
fi

source "$APP_DIR/venv/bin/activate"

cd "$APP_DIR"

nohup "$APP_DIR/venv/bin/python" -m uvicorn main:app --host "$HOST" --port "$PORT" > "$APP_DIR/app.log" 2>&1 &
echo $! > "$PID_FILE"

sleep 1

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "")
    echo "服务启动成功 (PID: $PID)"
    echo "本机访问: http://localhost:$PORT"
    if [ -n "$LAN_IP" ]; then
        echo "局域网访问: http://$LAN_IP:$PORT"
    fi
    echo "日志文件: $APP_DIR/app.log"
else
    echo "服务启动失败，请查看日志: $APP_DIR/app.log"
    rm -f "$PID_FILE"
    exit 1
fi