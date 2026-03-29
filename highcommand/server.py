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
    """List available MCP tools (raw, outcome-based, and analytics)."""
    return [
        # ----- Raw API (for custom analysis and raw stats questions) -----
        Tool(
            name="get_war_status",
            description="Raw war status from API. Use for custom analysis or when user asks for raw war data.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_planets",
            description="Raw planet list from API. Use for custom analysis or when user asks for raw planet data.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_statistics",
            description="Raw global statistics from API. Use for custom analysis or when user asks for raw stats.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_campaign_info",
            description="Raw active campaigns from API. Use for custom analysis.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_planet_status",
            description="Raw status for a specific planet by index.",
            inputSchema={
                "type": "object",
                "properties": {"planet_index": {"type": "integer", "description": "The index of the planet"}},
                "required": ["planet_index"],
            },
        ),
        Tool(
            name="get_biomes",
            description="Raw biome data from API.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_factions",
            description="Raw faction data from API.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_raw_api",
            description="Return raw API response for one endpoint. Use when user asks about raw stats or API messages. Endpoint: war/status, planets, statistics, campaigns/active, biomes, factions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "One of: war/status, planets, statistics, campaigns/active, biomes, factions",
                    },
                    "planet_index": {"type": "integer", "description": "Optional; for planets endpoint, fetch this planet's detail"},
                },
                "required": ["endpoint"],
            },
        ),
        # ----- Outcome-based tools -----
        Tool(
            name="get_war_summary",
            description="Human-readable war summary and current phase. Use when user asks: What's the state of the war?",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_where_to_deploy",
            description="Planets that need reinforcements most. Use when user asks: Where should I deploy?",
            inputSchema={
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "Max number of recommendations (default 10)"}},
                "required": [],
            },
        ),
        Tool(
            name="get_liberation_priority",
            description="Ordered list of planets by liberation priority. Use when user asks: What to liberate first?",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max number of planets (default 10)"},
                    "sector": {"type": "string", "description": "Filter by sector name"},
                },
                "required": [],
            },
        ),
        Tool(
            name="get_mission_efficiency_snapshot",
            description="Current mission efficiency (success rate, time, kills). Use when user asks: How are we doing on missions?",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        # ----- Analytics tools -----
        Tool(
            name="get_mission_analytics",
            description="Derived mission analytics: success rate, missions won/lost, mission time, kills breakdown. Use for efficiency or raw stats questions.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_war_analytics",
            description="War-level analytics: time left, active campaigns count, progress. Use for war overview.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_planet_analytics",
            description="Planet analytics by sector/owner and planets under attack. Use when user asks: Which sectors need help?",
            inputSchema={
                "type": "object",
                "properties": {
                    "sector": {"type": "string", "description": "Filter by sector"},
                    "group_by": {"type": "string", "description": "sector or owner"},
                },
                "required": [],
            },
        ),
        Tool(
            name="query_stats",
            description="Answer a single stats question. Use when user asks for one metric. Metric: mission_success_rate, missions_won, missions_lost, mission_time, time_played, bug_kills, automaton_kills, illuminate_kills, deaths, revives, accuracy, bullets_fired, bullets_hit, friendly_kills.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "description": "Metric key, e.g. mission_success_rate, bug_kills, deaths",
                    }
                },
                "required": ["metric"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute an MCP tool."""
    logger.info(f"Calling tool: {name}")

    try:
        # Raw API tools
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
        elif name == "get_raw_api":
            endpoint = arguments.get("endpoint")
            if not endpoint:
                raise ValueError("endpoint is required")
            result = await tools.get_raw_api_tool(
                endpoint=str(endpoint),
                planet_index=arguments.get("planet_index"),
            )
        # Outcome-based tools
        elif name == "get_war_summary":
            result = await tools.get_war_summary_tool()
        elif name == "get_where_to_deploy":
            result = await tools.get_where_to_deploy_tool(
                limit=int(arguments.get("limit", 10)),
            )
        elif name == "get_liberation_priority":
            result = await tools.get_liberation_priority_tool(
                limit=int(arguments.get("limit", 10)),
                sector=arguments.get("sector"),
            )
        elif name == "get_mission_efficiency_snapshot":
            result = await tools.get_mission_efficiency_snapshot_tool()
        # Analytics tools
        elif name == "get_mission_analytics":
            result = await tools.get_mission_analytics_tool()
        elif name == "get_war_analytics":
            result = await tools.get_war_analytics_tool()
        elif name == "get_planet_analytics":
            result = await tools.get_planet_analytics_tool(
                sector=arguments.get("sector"),
                group_by=arguments.get("group_by"),
            )
        elif name == "query_stats":
            metric = arguments.get("metric")
            if not metric:
                raise ValueError("metric is required")
            result = await tools.query_stats_tool(metric=str(metric))
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
