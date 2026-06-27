@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set APP_DIR=%SCRIPT_DIR%mysql_web_console
set PID_FILE=%APP_DIR%\.uvicorn.pid

if not exist "%PID_FILE%" (
    echo PID 文件不存在，尝试通过端口查找进程...

    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
        set FOUND_PID=%%a
        goto :kill_pid
    )
    echo 未找到监听 8000 端口的进程，服务可能未在运行
    pause
    exit /b 1
)

set /p PID=<"%PID_FILE%"

tasklist /fi "pid eq %PID%" 2>nul | findstr /i "%PID%" >nul
if %errorlevel% neq 0 (
    echo 进程 %PID% 已不存在，清理 PID 文件
    del "%PID_FILE%" 2>nul
    pause
    exit /b 1
)

:kill_pid
if not defined FOUND_PID set FOUND_PID=%PID%

echo 正在停止服务 (PID: %FOUND_PID%)...

taskkill /pid %FOUND_PID% >nul 2>&1
if %errorlevel%==0 (
    echo 服务已停止
) else (
    echo 优雅停止失败，尝试强制终止...
    taskkill /f /pid %FOUND_PID% >nul 2>&1
    if %errorlevel%==0 (
        echo 服务已强制停止
    ) else (
        echo 无法终止进程 %FOUND_PID%
    )
)

del "%PID_FILE%" 2>nul
if exist "%PID_FILE%" (
    echo PID 文件清理失败
) else (
    echo PID 文件已清理
)

echo.
pause