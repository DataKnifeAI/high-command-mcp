"""MCP Server implementation for Helldivers 2 API."""

import asyncio
import json
import logging
import os
import sys

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import (
    ServerCapabilities,
    TextContent,
    Tool,
)

from highcommand.tools import HighCommandTools

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Initialize server and tools
server = Server("high-command")
tools = HighCommandTools()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_war_status",
            description="Get current war status from High-Command API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_planets",
            description="Get planet information from High-Command API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_statistics",
            description="Get global game statistics from High-Command API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_campaign_info",
            description="Get campaign information from High-Command API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_planet_status",
            description="Get status for a specific planet",
            inputSchema={
                "type": "object",
                "properties": {
                    "planet_index": {
                        "type": "integer",
                        "description": "The index of the planet",
                    }
                },
                "required": ["planet_index"],
            },
        ),
        Tool(
            name="get_biomes",
            description="Get biome information from High-Command API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_factions",
            description="Get faction information from High-Command API",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute an MCP tool."""
    logger.info(f"Calling tool: {name}")

    try:
        if name == "get_war_status":
            result = await tools.get_war_status_tool()
        elif name == "get_planets":
            result = await tools.get_planets_tool()
        elif name == "get_statistics":
            result = await tools.get_statistics_tool()
        elif name == "get_campaign_info":
            result = await tools.get_campaign_info_tool()
        elif name == "get_planet_status":
            planet_index = arguments.get("planet_index")
            if planet_index is None:
                raise ValueError("planet_index is required")
            result = await tools.get_planet_status_tool(planet_index)
        elif name == "get_biomes":
            result = await tools.get_biomes_tool()
        elif name == "get_factions":
            result = await tools.get_factions_tool()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result))]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e!s}")
        return [
            TextContent(
                type="text",
                text=json.dumps({"status": "error", "data": None, "error": str(e)}),
            )
        ]


async def main():
    """Run the MCP server."""
    logger.info("Starting Helldivers 2 MCP Server")
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server started successfully and waiting for connections...")
        init_options = InitializationOptions(
            server_name="high-command",
            server_version="0.1.0",
            capabilities=ServerCapabilities(tools={}),
        )
        await server.run(read_stream, write_stream, init_options)


async def http_server():
    """Run the MCP server with HTTP/SSE transport (Kubernetes-ready)."""
    try:
        import uvicorn
        from fastapi import FastAPI, Request
        from fastapi.responses import StreamingResponse
    except ImportError:
        logger.error(
            "HTTP support requires 'uvicorn' and 'fastapi'. "
            "Install with: pip install high-command[http]"
        )
        sys.exit(1)

    app = FastAPI(title="High-Command MCP Server")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "high-command-mcp"}

    @app.get("/sse")
    async def sse_endpoint(request: Request):
        """SSE endpoint for MCP communication."""

        async def event_generator():
            """Generate MCP events over SSE."""
            transport = SseServerTransport(request.scope["client"][0])
            try:
                logger.info(f"New SSE connection from {request.scope['client'][0]}")
                init_options = InitializationOptions(
                    server_name="high-command",
                    server_version="0.1.0",
                    capabilities=ServerCapabilities(tools={}),
                )
                await server.run(transport.read_stream, transport.write_stream, init_options)
            except Exception as e:
                logger.error(f"SSE connection error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            finally:
                logger.info(f"SSE connection closed from {request.scope['client'][0]}")

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.post("/messages")
    async def handle_message(request: Request):
        """Handle JSON-RPC messages over HTTP."""
        try:
            data = await request.json()
            logger.debug(f"Received message: {data}")

            # Simulate MCP message handling
            if data.get("jsonrpc") == "2.0":
                method = data.get("method", "")
                params = data.get("params", {})

                if method == "tools/list":
                    # Return list of tools
                    result = await list_tools()
                    return {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {"tools": [t.model_dump() for t in result]},
                    }
                elif method == "tools/call":
                    # Call a tool
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await call_tool(tool_name, arguments)
                    return {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {"content": [r.model_dump() for r in result]},
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "error": {"code": -32601, "message": f"Method not found: {method}"},
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "error": {"code": -32600, "message": "Invalid Request"},
                }

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {e!s}"},
            }

    # Get configuration from environment
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    workers = int(os.getenv("MCP_WORKERS", "4"))

    logger.info(f"Starting HTTP MCP Server on {host}:{port}")

    # Run with uvicorn
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    # Determine transport mode
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        asyncio.run(http_server())
    elif transport == "sse":
        asyncio.run(http_server())
    else:
        # Default to stdio
        asyncio.run(main())
