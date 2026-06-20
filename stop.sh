#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/mysql_web_console"
PID_FILE="$APP_DIR/.uvicorn.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "PID 文件不存在，服务可能未在运行"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "进程 $PID 已不存在，清理 PID 文件"
    rm -f "$PID_FILE"
    exit 1
fi

echo "正在停止服务 (PID: $PID)..."
kill "$PID"

TIMEOUT=10
while [ $TIMEOUT -gt 0 ]; do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "服务已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
    TIMEOUT=$((TIMEOUT - 1))
done

echo "优雅停止超时，强制终止进程..."
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "服务已强制停止"