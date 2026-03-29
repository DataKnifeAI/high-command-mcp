"""Analytics module: derived metrics for mission efficiency and war/planet stats."""

from typing import Any

# Metric keys supported by query_stat_metric (map to statistics payload keys)
STAT_METRIC_KEYS = {
    "mission_success_rate": ("missionSuccessRate", "%", "Mission success rate (percentage)"),
    "missions_won": ("missionsWon", "", "Total missions won"),
    "missions_lost": ("missionsLost", "", "Total missions lost"),
    "mission_time": ("missionTime", "s", "Total mission time (seconds)"),
    "time_played": ("timePlayed", "s", "Total time played (seconds)"),
    "bug_kills": ("bugKills", "", "Terminid/bug kills"),
    "automaton_kills": ("automatonKills", "", "Automaton kills"),
    "illuminate_kills": ("illuminateKills", "", "Illuminate kills"),
    "bullets_fired": ("bulletsFired", "", "Bullets fired"),
    "bullets_hit": ("bulletsHit", "", "Bullets hit"),
    "accuracy": ("accuracy", "%", "Accuracy (percentage)"),
    "deaths": ("deaths", "", "Total deaths"),
    "revives": ("revives", "", "Revives"),
    "friendly_kills": ("friendlyKills", "", "Friendly kills"),
}


def _get_data(payload: dict[str, Any]) -> Any:
    """Extract data from API response envelope."""
    if payload is None:
        return None
    return payload.get("data") if isinstance(payload, dict) else payload


def mission_analytics(raw_stats_response: dict[str, Any]) -> dict[str, Any]:
    """Derive mission analytics from global statistics API response.

    Returns outcome, summary, success_rate, missions_won/lost, mission_time, kills.
    """
    data = _get_data(raw_stats_response)
    if not data:
        return {
            "outcome": "no_data",
            "summary": "No statistics data available.",
            "success_rate": None,
            "missions_won": None,
            "missions_lost": None,
            "mission_time": None,
            "kills": None,
            "data": raw_stats_response,
        }

    # API may return list of one stats object or single object
    if isinstance(data, list) and len(data) > 0:
        stats = data[0]
    elif isinstance(data, dict):
        stats = data
    else:
        return {
            "outcome": "no_data",
            "summary": "Statistics format not recognized.",
            "data": raw_stats_response,
        }

    missions_won = stats.get("missionsWon", 0) or 0
    missions_lost = stats.get("missionsLost", 0) or 0
    total = missions_won + missions_lost
    success_rate = round(100 * missions_won / total, 1) if total else None

    return {
        "outcome": "ok",
        "summary": (
            f"Mission success rate: {success_rate}% ({missions_won:,} won, {missions_lost:,} lost). "
            f"Total mission time: {stats.get('missionTime', 0):,}s. "
            f"Kills: Bugs {stats.get('bugKills', 0):,}, Automatons {stats.get('automatonKills', 0):,}, Illuminate {stats.get('illuminateKills', 0):,}."
        ),
        "success_rate": success_rate,
        "missions_won": missions_won,
        "missions_lost": missions_lost,
        "mission_time": stats.get("missionTime"),
        "time_played": stats.get("timePlayed"),
        "kills": {
            "bugKills": stats.get("bugKills"),
            "automatonKills": stats.get("automatonKills"),
            "illuminateKills": stats.get("illuminateKills"),
        },
        "data": stats,
    }


def war_analytics(
    war_status_response: dict[str, Any],
    campaigns_response: dict[str, Any] | None = None,
    planets_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """War-level analytics: time left, active campaigns count, high-level progress."""
    war_data = _get_data(war_status_response)
    campaigns_data = _get_data(campaigns_response) if campaigns_response else None
    planets_data = _get_data(planets_response) if planets_response else None

    if not war_data and not campaigns_data:
        return {
            "outcome": "no_data",
            "summary": "No war or campaign data available.",
            "time_left": None,
            "active_campaigns": None,
            "data": {
                "war": war_data,
                "campaigns": campaigns_data,
            },
        }

    active_campaigns = 0
    if campaigns_data is not None:
        active_campaigns = len(campaigns_data) if isinstance(campaigns_data, list) else (1 if campaigns_data else 0)

    time_left = None
    war_id = None
    if isinstance(war_data, dict):
        war_id = war_data.get("id") or war_data.get("index")
        end_date = war_data.get("endDate")
        if end_date:
            try:
                from datetime import datetime, timezone
                if isinstance(end_date, str):
                    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                else:
                    end = end_date
                now = datetime.now(timezone.utc)
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                delta = end - now
                time_left = max(0, int(delta.total_seconds()))
            except Exception:
                pass

    summary_parts = []
    if war_id is not None:
        summary_parts.append(f"War {war_id} active.")
    if time_left is not None:
        days = time_left // 86400
        summary_parts.append(f"Time remaining: {days} days.")
    summary_parts.append(f"Active campaigns: {active_campaigns}.")
    summary = " ".join(summary_parts)

    return {
        "outcome": "ok",
        "summary": summary,
        "time_left_seconds": time_left,
        "active_campaigns": active_campaigns,
        "war_id": war_id,
        "data": {
            "war": war_data,
            "campaigns": campaigns_data,
            "planets_count": len(planets_data) if isinstance(planets_data, list) else None,
        },
    }


def planet_analytics(
    planets_response: dict[str, Any],
    campaigns_response: dict[str, Any] | None = None,
    sector: str | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Per-planet or aggregate planet analytics: by sector, by owner, etc."""
    planets_data = _get_data(planets_response)
    campaigns_data = _get_data(campaigns_response) if campaigns_response else None

    if not planets_data or not isinstance(planets_data, list):
        return {
            "outcome": "no_data",
            "summary": "No planet data available.",
            "by_sector": {},
            "by_owner": {},
            "data": planets_data,
        }

    campaign_planet_indices = set()
    if isinstance(campaigns_data, list):
        for c in campaigns_data:
            if isinstance(c, dict) and "planet" in c:
                campaign_planet_indices.add(c["planet"])

    by_sector: dict[str, int] = {}
    by_owner: dict[str, int] = {}
    filtered = planets_data
    if sector:
        filtered = [p for p in planets_data if isinstance(p, dict) and p.get("sector") == sector]

    for p in filtered:
        if not isinstance(p, dict):
            continue
        sec = p.get("sector") or "Unknown"
        by_sector[sec] = by_sector.get(sec, 0) + 1
        owner = "Unknown"
        if "status" in p and isinstance(p["status"], dict):
            owner = p["status"].get("owner") or owner
        by_owner[owner] = by_owner.get(owner, 0) + 1

    under_attack = [p for p in filtered if isinstance(p, dict) and p.get("index") in campaign_planet_indices]
    summary = (
        f"{len(filtered)} planets total. "
        f"Sectors: {len(by_sector)}. "
        f"{len(under_attack)} planets with active campaigns."
    )

    result = {
        "outcome": "ok",
        "summary": summary,
        "by_sector": by_sector,
        "by_owner": by_owner,
        "planets_with_campaigns": len(under_attack),
        "data": {"count": len(filtered), "by_sector": by_sector, "by_owner": by_owner},
    }
    if group_by == "sector":
        result["grouped"] = by_sector
    elif group_by == "owner":
        result["grouped"] = by_owner
    return result


def query_stat_metric(raw_stats_response: dict[str, Any], metric_key: str) -> dict[str, Any]:
    """Answer a single stats question. metric_key e.g. mission_success_rate, deaths, time_played."""
    data = _get_data(raw_stats_response)
    if not data:
        return {
            "outcome": "no_data",
            "answer": "No statistics data available.",
            "value": None,
            "unit": None,
            "data": None,
        }

    if isinstance(data, list) and len(data) > 0:
        stats = data[0]
    elif isinstance(data, dict):
        stats = data
    else:
        return {
            "outcome": "no_data",
            "answer": "Statistics format not recognized.",
            "value": None,
            "unit": None,
            "data": None,
        }

    key_lower = metric_key.strip().lower().replace(" ", "_")
    if key_lower not in STAT_METRIC_KEYS:
        valid = ", ".join(STAT_METRIC_KEYS.keys())
        return {
            "outcome": "unknown_metric",
            "answer": f"Unknown metric '{metric_key}'. Valid metrics: {valid}.",
            "value": None,
            "unit": None,
            "data": None,
        }

    api_key, unit, description = STAT_METRIC_KEYS[key_lower]
    value = stats.get(api_key)
    if value is None:
        value = stats.get(api_key)  # try as-is

    return {
        "outcome": "ok",
        "answer": f"{description}: {value} {unit}".strip() if value is not None else f"{description}: no value",
        "value": value,
        "unit": unit,
        "metric": key_lower,
        "data": {api_key: value},
    }
