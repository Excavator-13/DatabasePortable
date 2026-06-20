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

source "$APP_DIR/venv/bin/activate"

cd "$APP_DIR"

nohup python -m uvicorn main:app --host "$HOST" --port "$PORT" > "$APP_DIR/app.log" 2>&1 &
echo $! > "$PID_FILE"

sleep 1

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    echo "服务启动成功 (PID: $PID)"
    echo "访问地址: http://localhost:$PORT"
    echo "日志文件: $APP_DIR/app.log"
else
    echo "服务启动失败，请查看日志: $APP_DIR/app.log"
    rm -f "$PID_FILE"
    exit 1
fi