"""FastAPI + FastMCP application for the mock Collibra pre-flight server."""

from fastapi import FastAPI
from fastmcp import FastMCP

from server.tools import register_tools

mcp_server = FastMCP(
    "Collibra Pre-Flight Check",
    instructions=(
        "You are a data governance assistant. Use the pre-flight check tools "
        "to validate data products before they are used in analytics or ML pipelines. "
        "Always run a full pre-flight check when asked about data product readiness."
    ),
)

register_tools(mcp_server)

mcp_app = mcp_server.http_app(stateless_http=True)

app = FastAPI(
    title="Collibra Pre-Flight Check MCP",
    description="Mock Collibra pre-flight checks for Databricks Apps",
    version="0.1.0",
    lifespan=mcp_app.lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "collibra-preflight-check"}


combined_app = FastAPI(
    title="Combined MCP App",
    routes=[
        *mcp_app.routes,
        *app.routes,
    ],
    lifespan=mcp_app.lifespan,
)
