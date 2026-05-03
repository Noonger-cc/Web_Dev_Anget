@echo off
chcp 65001 >nul
echo ============================================
echo    LangGraph 智能运维 Agent - 安装依赖脚本
echo ============================================
echo.

echo [1/3] 安装 Python 依赖...
cd /d %~dp0agent-py
pip install -r requirements.txt
echo Python 依赖安装完成！
echo.

echo [2/3] 安装 Node.js 依赖...
cd /d %~dp0web
npm install
echo Node.js 依赖安装完成！
echo.

echo [3/3] 下载 Go 依赖...
cd /d %~dp0server-go
go env -w GOPROXY=https://goproxy.cn,direct
go env -w GOSUMDB=off
go mod tidy
echo Go 依赖下载完成！
echo.

echo ============================================
echo    所有依赖安装完成！
echo ============================================
echo.
echo 现在可以运行 start.bat 启动服务！
echo.
echo 按任意键关闭此窗口...
pause >nul