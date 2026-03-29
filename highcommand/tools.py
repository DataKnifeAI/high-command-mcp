"""MCP tools for High-Command API."""

import inspect
import time
from typing import Any, Callable

import structlog

from highcommand import analytics, outcomes
from highcommand.api_client import HighCommandAPIClient

logger = structlog.get_logger(__name__)

# Endpoints supported by get_raw_api
RAW_API_ENDPOINTS = frozenset({
    "war/status", "planets", "statistics", "campaigns/active", "biomes", "factions",
})


def _envelope(
    status: str,
    outcome: str | None = None,
    summary: str | None = None,
    data: Any = None,
    error: str | None = None,
    elapsed_ms: float | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build agent-friendly response envelope."""
    out = {
        "status": status,
        "outcome": outcome,
        "summary": summary,
        "data": data,
        "error": error,
    }
    if elapsed_ms is not None:
        out["metrics"] = {"elapsed_ms": round(elapsed_ms, 2)}
    for k, v in extra.items():
        if k not in out and v is not None:
            out[k] = v
    return out


class HighCommandTools:
    """Tools for interacting with High-Command API."""

    @staticmethod
    async def _run_tool(func: Callable[..., Any], include_metrics: bool = False) -> dict[str, Any]:
        """Helper to run a tool function with standardized response shape.

        Args:
            func: Async callable that returns tool data
            include_metrics: Whether to include execution metrics in response

        Returns:
            Standardized response with status, data, and error fields

        Raises:
            TypeError: If func is not a coroutine function
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"Expected async function, got {type(func).__name__}")

        start_time = time.perf_counter()
        try:
            data = await func()
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            response = {"status": "success", "data": data, "error": None}

            if include_metrics:
                response["metrics"] = {"elapsed_ms": elapsed_ms}

            return response
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            error_type = type(e).__name__
            error_msg = f"{error_type}: {e!s}"

            # Log the error with context
            logger.error(
                "Tool execution failed",
                error_type=error_type,
                error_msg=str(e),
                elapsed_ms=elapsed_ms,
            )

            response = {"status": "error", "data": None, "error": error_msg}

            if include_metrics:
                response["metrics"] = {"elapsed_ms": elapsed_ms}

            return response

    async def get_war_status_tool(self) -> dict[str, Any]:
        """Tool to get current war status.

        Returns:
            JSON formatted war status
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_war_status()

        return await self._run_tool(_fetch)

    async def get_planets_tool(self) -> dict[str, Any]:
        """Tool to get planet information.

        Returns:
            JSON formatted planet data
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_planets()

        return await self._run_tool(_fetch)

    async def get_statistics_tool(self) -> dict[str, Any]:
        """Tool to get global statistics.

        Returns:
            JSON formatted statistics data
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_statistics()

        return await self._run_tool(_fetch)

    async def get_campaign_info_tool(self) -> dict[str, Any]:
        """Tool to get campaign information.

        Returns:
            JSON formatted campaign data
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_campaign_info()

        return await self._run_tool(_fetch)

    async def get_planet_status_tool(self, planet_index: int) -> dict[str, Any]:
        """Tool to get status for a specific planet.

        Args:
            planet_index: Index of the planet

        Returns:
            JSON formatted planet status data
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_planet_status(planet_index)

        return await self._run_tool(_fetch)

    async def get_biomes_tool(self) -> dict[str, Any]:
        """Tool to get biome information.

        Returns:
            JSON formatted biome data
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_biomes()

        return await self._run_tool(_fetch)

    async def get_factions_tool(self) -> dict[str, Any]:
        """Tool to get faction information.

        Returns:
            JSON formatted faction data
        """

        async def _fetch() -> Any:
            async with HighCommandAPIClient() as client:
                return await client.get_factions()

        return await self._run_tool(_fetch)

    # ---------- Raw API (single entry point for raw stats/messages) ----------

    async def get_raw_api_tool(self, endpoint: str, planet_index: int | None = None) -> dict[str, Any]:
        """Return raw API response for one endpoint. Use when the user asks about raw stats or API messages."""
        start = time.perf_counter()
        try:
            if endpoint not in RAW_API_ENDPOINTS:
                return _envelope(
                    "error",
                    outcome="invalid_endpoint",
                    summary=f"Unknown endpoint. Use one of: {', '.join(sorted(RAW_API_ENDPOINTS))}.",
                    data=None,
                    error=f"Unknown endpoint: {endpoint}",
                    elapsed_ms=(time.perf_counter() - start) * 1000,
                    endpoint=endpoint,
                )
            async with HighCommandAPIClient() as client:
                if endpoint == "war/status":
                    data = await client.get_war_status()
                elif endpoint == "planets":
                    data = await client.get_planet_status(planet_index) if planet_index is not None else await client.get_planets()
                elif endpoint == "statistics":
                    data = await client.get_statistics()
                elif endpoint == "campaigns/active":
                    data = await client.get_campaign_info()
                elif endpoint == "biomes":
                    data = await client.get_biomes()
                elif endpoint == "factions":
                    data = await client.get_factions()
                else:
                    return _envelope(
                        "error",
                        outcome="invalid_endpoint",
                        summary=f"Unknown endpoint: {endpoint}",
                        data=None,
                        error=f"Unknown endpoint: {endpoint}",
                        elapsed_ms=(time.perf_counter() - start) * 1000,
                        endpoint=endpoint,
                    )
            elapsed_ms = (time.perf_counter() - start) * 1000
            return _envelope(
                "success",
                outcome="ok",
                summary="Raw API response for custom analysis.",
                data=data,
                error=None,
                elapsed_ms=elapsed_ms,
                endpoint=endpoint,
            )
        except Exception as e:
            logger.error("get_raw_api failed", endpoint=endpoint, error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
                endpoint=endpoint,
            )

    # ---------- Outcome-based tools ----------

    async def get_war_summary_tool(self) -> dict[str, Any]:
        """Human-readable war summary and current phase. Outcome: What's the state of the war?"""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                war = await client.get_war_status()
            result = outcomes.war_summary(war)
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_war_summary failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    async def get_where_to_deploy_tool(self, limit: int = 10) -> dict[str, Any]:
        """Planets that need reinforcements most. Outcome: Where should I deploy?"""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                campaigns = await client.get_campaign_info()
                planets = await client.get_planets()
            result = outcomes.where_to_deploy(campaigns, planets, limit=limit)
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_where_to_deploy failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    async def get_liberation_priority_tool(
        self, limit: int = 10, sector: str | None = None
    ) -> dict[str, Any]:
        """Ordered list of planets by liberation priority. Outcome: What to liberate first?"""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                planets = await client.get_planets()
                campaigns = await client.get_campaign_info()
            result = outcomes.liberation_priority(
                planets, campaigns, limit=limit, sector=sector
            )
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_liberation_priority failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    async def get_mission_efficiency_snapshot_tool(self) -> dict[str, Any]:
        """Current mission efficiency from global stats. Outcome: How are we doing on missions?"""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                stats = await client.get_statistics()
            result = outcomes.mission_efficiency_snapshot(stats)
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_mission_efficiency_snapshot failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    # ---------- Analytics tools ----------

    async def get_mission_analytics_tool(self) -> dict[str, Any]:
        """Derived mission analytics: success rate, missions won/lost, mission time, kills breakdown."""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                stats = await client.get_statistics()
            result = analytics.mission_analytics(stats)
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_mission_analytics failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    async def get_war_analytics_tool(self) -> dict[str, Any]:
        """War-level analytics: time left, active campaigns count, progress indicators."""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                war = await client.get_war_status()
                campaigns = await client.get_campaign_info()
                planets = await client.get_planets()
            result = analytics.war_analytics(war, campaigns, planets)
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_war_analytics failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    async def get_planet_analytics_tool(
        self, sector: str | None = None, group_by: str | None = None
    ) -> dict[str, Any]:
        """Planet analytics: count by sector, by owner, planets under attack. Which sectors need help?"""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                planets = await client.get_planets()
                campaigns = await client.get_campaign_info()
            result = analytics.planet_analytics(
                planets, campaigns, sector=sector, group_by=group_by
            )
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("get_planet_analytics failed", error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    async def query_stats_tool(self, metric: str) -> dict[str, Any]:
        """Answer a single stats question. metric e.g. mission_success_rate, deaths, time_played, bug_kills."""
        start = time.perf_counter()
        try:
            async with HighCommandAPIClient() as client:
                stats = await client.get_statistics()
            result = analytics.query_stat_metric(stats, metric)
            return _envelope(
                "success",
                error=None,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                **result,
            )
        except Exception as e:
            logger.error("query_stats failed", metric=metric, error=str(e))
            return _envelope(
                "error",
                outcome="error",
                summary=str(e),
                data=None,
                error=str(e),
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )
