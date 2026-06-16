@echo off
cd /d "%~dp0"

echo Starting WebDown MCP Server...
echo MCP  -^> http://localhost:8002

:: Activate virtual environment and run
call .venv\Scripts\activate.bat

:: Force HTTP transport for client connectivity
set WEBDOWN_TRANSPORT=http
set WEBDOWN_HOST=127.0.0.1
set WEBDOWN_PORT=8002

python run_mcp.py

pause
