"""Convenience entry point — run with: python run_mcp.py

Starts the MCP server. Defaults to stdio transport.
Set WEBDOWN_TRANSPORT=http to run on port 8002.

All startup logic lives in webdown/startup/mcp.py (composition root).
"""

from webdown.startup.mcp import run

if __name__ == "__main__":
    run()
