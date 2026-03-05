"""Outcome module: high-level answers (war summary, where to deploy, liberation priority, efficiency)."""

from typing import Any


def _get_data(payload: dict[str, Any] | None) -> Any:
    if payload is None:
        return None
    return payload.get("data") if isinstance(payload, dict) else payload


def war_summary(war_status_response: dict[str, Any]) -> dict[str, Any]:
    """Human-readable war summary and current phase. Outcome: What's the state of the war?"""
    war_data = _get_data(war_status_response)
    if not war_data or not isinstance(war_data, dict):
        return {
            "outcome": "no_data",
            "summary": "No war status data available.",
            "war_id": None,
            "phase": None,
            "ends_at": None,
            "data": war_data,
        }

    war_id = war_data.get("id") or war_data.get("index")
    phase = "active"  # API may not expose phase; default
    ends_at = war_data.get("endDate")
    summary = f"War {war_id} is {phase}. End date: {ends_at}."
    return {
        "outcome": "ok",
        "summary": summary,
        "war_id": war_id,
        "phase": phase,
        "ends_at": ends_at,
        "data": war_data,
    }


def where_to_deploy(
    campaigns_response: dict[str, Any],
    planets_response: dict[str, Any],
    limit: int = 10,
) -> dict[str, Any]:
    """Planets/campaigns that need reinforcements most. Outcome: Where should I deploy?"""
    campaigns_data = _get_data(campaigns_response)
    planets_data = _get_data(planets_response)

    if not campaigns_data or not isinstance(campaigns_data, list):
        return {
            "outcome": "no_data",
            "summary": "No active campaign data available.",
            "recommendations": [],
            "data": None,
        }

    planets_list = planets_data if isinstance(planets_data, list) else []
    planet_by_index = {p.get("index"): p for p in planets_list if isinstance(p, dict)}

    recommendations = []
    for c in campaigns_data[: limit * 2]:  # allow extra to fill limit
        if not isinstance(c, dict):
            continue
        planet_index = c.get("planet")
        if planet_index is None:
            continue
        p = planet_by_index.get(planet_index)
        name = p.get("name", f"Planet {planet_index}") if p else f"Planet {planet_index}"
        sector = p.get("sector", "Unknown") if p else "Unknown"
        recommendations.append({
            "planet_index": planet_index,
            "name": name,
            "sector": sector,
            "reason": "Active campaign",
        })
        if len(recommendations) >= limit:
            break

    summary = f"{len(recommendations)} planets with active campaigns need reinforcements."
    if recommendations:
        names = ", ".join(r["name"] for r in recommendations[:5])
        if len(recommendations) > 5:
            names += f" and {len(recommendations) - 5} more"
        summary += f" Top: {names}."

    return {
        "outcome": "ok",
        "summary": summary,
        "recommendations": recommendations,
        "data": {"campaigns": campaigns_data, "count": len(recommendations)},
    }


def liberation_priority(
    planets_response: dict[str, Any],
    campaigns_response: dict[str, Any] | None = None,
    limit: int = 10,
    sector: str | None = None,
) -> dict[str, Any]:
    """Ordered list of planets by liberation priority. Outcome: What to liberate first?"""
    planets_data = _get_data(planets_response)
    campaigns_data = _get_data(campaigns_response) if campaigns_response else None

    if not planets_data or not isinstance(planets_data, list):
        return {
            "outcome": "no_data",
            "summary": "No planet data available.",
            "priorities": [],
            "data": None,
        }

    campaign_planet_indices = set()
    if isinstance(campaigns_data, list):
        for c in campaigns_data:
            if isinstance(c, dict) and "planet" in c:
                campaign_planet_indices.add(c["planet"])

    # Build priority: planets with active campaigns first, then by sector filter
    with_campaigns = []
    without = []
    for p in planets_data:
        if not isinstance(p, dict):
            continue
        if sector and p.get("sector") != sector:
            continue
        idx = p.get("index")
        name = p.get("name", f"Planet {idx}")
        rec = {"planet_index": idx, "name": name, "sector": p.get("sector"), "has_campaign": idx in campaign_planet_indices}
        if rec["has_campaign"]:
            with_campaigns.append(rec)
        else:
            without.append(rec)

    priorities = with_campaigns + without[: max(0, limit - len(with_campaigns))]
    priorities = priorities[:limit]

    summary = f"Top {len(priorities)} planets by liberation priority. {len(with_campaigns)} have active campaigns."
    return {
        "outcome": "ok",
        "summary": summary,
        "priorities": priorities,
        "data": {"count": len(priorities), "with_campaigns": len(with_campaigns)},
    }


def mission_efficiency_snapshot(statistics_response: dict[str, Any]) -> dict[str, Any]:
    """Current mission efficiency from global stats. Outcome: How are we doing on missions?"""
    data = _get_data(statistics_response)
    if not data:
        return {
            "outcome": "no_data",
            "summary": "No statistics data available.",
            "success_rate": None,
            "missions_won": None,
            "missions_lost": None,
            "time_played": None,
            "data": None,
        }

    if isinstance(data, list) and len(data) > 0:
        stats = data[0]
    elif isinstance(data, dict):
        stats = data
    else:
        return {
            "outcome": "no_data",
            "summary": "Statistics format not recognized.",
            "success_rate": None,
            "missions_won": None,
            "missions_lost": None,
            "time_played": None,
            "data": None,
        }

    missions_won = stats.get("missionsWon", 0) or 0
    missions_lost = stats.get("missionsLost", 0) or 0
    total = missions_won + missions_lost
    success_rate = round(100 * missions_won / total, 1) if total else stats.get("missionSuccessRate")

    summary = (
        f"Mission success rate: {success_rate}%. "
        f"Missions won: {missions_won:,}, lost: {missions_lost:,}. "
        f"Time played: {stats.get('timePlayed', 0):,}s."
    )
    return {
        "outcome": "ok",
        "summary": summary,
        "success_rate": success_rate,
        "missions_won": missions_won,
        "missions_lost": missions_lost,
        "time_played": stats.get("timePlayed"),
        "data": stats,
    }
