# PowerShell 启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动 Flask 后端服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 激活虚拟环境
& .\venv\Scripts\Activate.ps1

# 启动应用
python app.py

