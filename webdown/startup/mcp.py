"""MCP server startup — composition root for the MCP transport.

Clean architecture: this module creates the FastMCP server, bootstraps
dependencies, and provides the CLI runner. Tools live in presentation/mcp/.
"""

import logging
import os

from dotenv import load_dotenv

from webdown.startup.repository_factory import create_schema_initializer

load_dotenv()

logger = logging.getLogger(__name__)


def bootstrap() -> None:
    """Initialize database schemas for MCP usage."""
    create_schema_initializer().initialize()
    logger.info("MCP database initialized")


def get_transport_config() -> dict:
    """Read transport configuration from environment variables."""
    return {
        "transport": os.getenv("WEBDOWN_TRANSPORT", "stdio").lower(),
        "host": os.getenv("WEBDOWN_HOST", "127.0.0.1"),
        "port": int(os.getenv("WEBDOWN_PORT", "8002")),
    }


def run() -> None:
    """Start the MCP server. Called by CLI entry points."""
    from webdown.presentation.mcp.server import create_server

    bootstrap()
    server = create_server()
    config = get_transport_config()

    if config["transport"] == "http":
        logger.info("Starting MCP server on http://%s:%s", config["host"], config["port"])
        server.run(transport="streamable-http", host=config["host"], port=config["port"])
    else:
        logger.info("Starting MCP server on stdio")
        server.run(transport="stdio")
