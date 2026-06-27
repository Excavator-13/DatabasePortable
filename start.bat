@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set APP_DIR=%SCRIPT_DIR%mysql_web_console
set PID_FILE=%APP_DIR%\.uvicorn.pid
set HOST=0.0.0.0
set PORT=8000

if exist "%PID_FILE%" (
    set /p OLD_PID=<"%PID_FILE%"
    tasklist /fi "pid eq !OLD_PID!" 2>nul | findstr /i "!OLD_PID!" >nul
    if !errorlevel!==0 (
        echo 服务已在运行中 (PID: !OLD_PID!)
        echo 如需重新启动，请先执行 stop.bat
        exit /b 1
    )
    del "%PID_FILE%" 2>nul
)

echo 正在启动 MySQL Web Console...

call "%APP_DIR%\venv\Scripts\activate.bat"

cd /d "%APP_DIR%"

powershell -Command "$p = Start-Process -FilePath '%APP_DIR%\venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','main:app','--host','%HOST%','--port','%PORT%' -RedirectStandardOutput '%APP_DIR%\app.log' -RedirectStandardError '%APP_DIR%\app.log' -PassThru -WindowStyle Hidden; $p.Id | Out-File -FilePath '%PID_FILE%' -NoNewline"

timeout /t 2 /nobreak >nul

if not exist "%PID_FILE%" (
    echo 服务启动失败，请检查日志: %APP_DIR%\app.log
    pause
    exit /b 1
)

set /p PID=<"%PID_FILE%"
tasklist /fi "pid eq %PID%" 2>nul | findstr /i "%PID%" >nul
if %errorlevel%==0 (
    echo.
    echo ============================================
    echo   服务启动成功 (PID: %PID%)
    echo   本机访问: http://localhost:%PORT%
    echo   日志文件: %APP_DIR%\app.log
    echo.
    echo   如需停止服务，请执行 stop.bat
    echo ============================================
    echo.

    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
        set LAN_IP=%%a
        set LAN_IP=!LAN_IP: =!
        if not "!LAN_IP!"=="" (
            echo 局域网访问: http://!LAN_IP!:!PORT!
        )
    )
) else (
    echo 服务启动失败，请查看日志: %APP_DIR%\app.log
    del "%PID_FILE%" 2>nul
)

echo.
pause