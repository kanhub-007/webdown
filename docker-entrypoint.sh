#!/bin/bash
set -e

echo "Starting WebDown..."
echo "Mode: ${APP_MODE:-api}"

case "${APP_MODE:-api}" in
    api)
        echo "Starting API server..."
        exec python -m uvicorn webdown.startup.api:app --host 0.0.0.0 --port "${API_PORT:-8000}"
        ;;
    mcp)
        echo "Starting MCP server (HTTP transport)..."
        export WEBDOWN_TRANSPORT=http
        export WEBDOWN_HOST="${WEBDOWN_HOST:-0.0.0.0}"
        export WEBDOWN_PORT="${WEBDOWN_PORT:-8002}"
        exec python run_mcp.py
        ;;
    all)
        echo "Starting API + MCP..."
        export WEBDOWN_TRANSPORT=http
        export WEBDOWN_HOST="${WEBDOWN_HOST:-0.0.0.0}"
        export WEBDOWN_PORT="${WEBDOWN_PORT:-8002}"
        python -m uvicorn webdown.startup.api:app --host 0.0.0.0 --port "${API_PORT:-8000}" &
        sleep 2
        exec python run_mcp.py
        ;;
    *)
        echo "Unknown APP_MODE: ${APP_MODE}. Use api, mcp, or all."
        exit 1
        ;;
esac
