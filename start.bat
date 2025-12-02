@echo off
echo ========================================
echo 启动 Flask 后端服务
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动应用
python app.py

pause

