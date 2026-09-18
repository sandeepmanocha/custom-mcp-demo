"""Entry point for the MCP server."""

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("DATABRICKS_APP_PORT", "8000"))
    uvicorn.run(
        "server.app:combined_app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
