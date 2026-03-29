# MCP Tools Review: Outcome-Based, Agent-Friendly, and Analytics

**Goal**: Tools that are outcome-based and agent-friendly, with analytics so users can ask questions about raw stats and API data and complete goals/missions more efficiently.

---

## 1. Current State

### Existing tools (endpoint-centric, raw data)

| Tool | Purpose | Agent-friendly? | Outcome-based? |
|------|---------|-----------------|----------------|
| `get_war_status` | Raw war status JSON | Low – agent must interpret | No |
| `get_planets` | Raw planets list | Low | No |
| `get_statistics` | Raw global stats | Low | No |
| `get_campaign_info` | Raw active campaigns | Low | No |
| `get_planet_status` | Raw single-planet status | Low | No |
| `get_biomes` | Raw biomes | Low | No |
| `get_factions` | Raw factions | Low | No |

**Gaps**:

- **Outcome-based**: No tools that answer “what should I do?” or “what’s the outcome?” (e.g. where to deploy, war summary, priority missions).
- **Analytics**: No derived metrics for efficiency (success rates, best sectors, mission effectiveness, time-to-liberate).
- **Queryable raw data**: Raw JSON is returned but there’s no structured “ask a question about stats/messages” surface—agents get dumps and must parse everything themselves.

---

## 2. Design Principles

### Outcome-based

- **Input**: Minimal or high-level (e.g. “current war”, “where to help”).
- **Output**: Clear **outcome** or **recommendation**, not raw payloads.
- **Examples**: “War summary”, “Planets that need reinforcements”, “Best missions for impact”, “Liberation priority list”.

### Agent-friendly

- **Stable, documented response shape**: Same top-level keys (`outcome`, `summary`, `recommendations`, `data`, `error`) so agents can branch on success/error and use fields reliably.
- **Structured text + optional structured data**: Short `summary` for LLM context; optional `data` for programmatic use.
- **Explicit semantics**: Tool names and descriptions state the outcome (e.g. “Get planets that need reinforcements” not “Get campaign info”).
- **Single-call outcomes**: One tool call returns a complete answer when possible, reducing round-trips and reasoning load.

### Analytics for efficient goals/missions

- **Derived metrics** from raw API data:
  - Mission efficiency: success rate, time per mission, kills per hour.
  - War progress: liberation trend, sector pressure, campaign completion.
  - Impact: which planets/campaigns contribute most to war progress.
- **Answers to questions** like:
  - “How efficiently are we completing missions?” (success rate, time, etc.)
  - “Which sectors need the most help?”
  - “What do the latest stats say about bug vs automaton kills?”

---

## 3. Proposed Tool Layout

### A. Keep: Raw data access (for “questions on raw stats and messages”)

Keep existing tools as the **raw API layer**, but clarify their role:

- **Purpose**: “Get raw stats and API messages so the user/agent can ask arbitrary questions.”
- **Naming**: Optional rename for clarity (e.g. keep `get_statistics` but describe as “Raw global statistics from the API for custom analysis”).

Add one optional **query-style** tool so agents can request “one place” for raw data:

| Tool | Description | Parameters | Returns |
|------|-------------|------------|--------|
| `get_raw_api` | Return raw API response for one known endpoint. Use when the user asks about raw stats or API messages. | `endpoint`: one of `war/status`, `planets`, `statistics`, `campaigns/active`, `biomes`, `factions`; optional `planet_index` for planet detail | `{ "status", "data", "error", "endpoint" }` |

This gives a single, consistent way to “ask questions on raw stats and messages” without adding many new endpoints.

### B. New: Outcome-based tools

High-level answers; one call = one outcome.

| Tool | Description | Parameters | Returns (conceptual) |
|------|-------------|------------|----------------------|
| `get_war_summary` | Human-readable war summary and current phase. Outcome: “What’s the state of the war?” | None | `outcome`, `summary`, `war_id`, `phase`, `ends_at`, optional `data` |
| `get_where_to_deploy` | Planets (or campaigns) that need reinforcements most. Outcome: “Where should I deploy?” | Optional `limit` | `outcome`, `summary`, `recommendations` (list of planet/campaign + reason), optional `data` |
| `get_liberation_priority` | Ordered list of planets by liberation priority (e.g. by health, campaign count, sector). Outcome: “What to liberate first?” | Optional `limit`, `sector` | `outcome`, `summary`, `priorities` (list), optional `data` |
| `get_mission_efficiency_snapshot` | Current mission efficiency (from global stats): success rate, time played, kills. Outcome: “How are we doing on missions?” | None | `outcome`, `summary`, `success_rate`, `missions_won/lost`, `time_played`, optional `data` |

All return a **stable envelope**: `outcome` (e.g. "ok" / "no_data"), `summary` (text), then outcome-specific fields, plus optional `data` for raw-ish detail.

### C. New: Analytics tools

Derived metrics and answers for “efficiently complete goals and missions” and “questions on raw stats”.

| Tool | Description | Parameters | Returns (conceptual) |
|------|-------------|------------|----------------------|
| `get_mission_analytics` | Derived mission analytics: success rate, missions won/lost, mission time, kills breakdown (bugs/automatons/illuminate). Use for “efficiency” and “raw stats” questions. | None | `outcome`, `summary`, `success_rate`, `missions_won`, `missions_lost`, `mission_time`, `kills`, optional `data` (raw stats slice) |
| `get_war_analytics` | War-level analytics: time left, progress indicators (if API supports), active campaigns count, planets under attack. | None | `outcome`, `summary`, `time_left`, `active_campaigns`, optional `data` |
| `get_planet_analytics` | Per-planet or aggregate planet analytics: e.g. count by sector, by owner, under attack. Enables “which sectors need help?” | Optional `sector`, `group_by` | `outcome`, `summary`, `by_sector` / `by_owner`, optional `data` |
| `query_stats` | Answer a simple stats question from global statistics. Accepts a question type or key (e.g. “mission_success_rate”, “bug_kills”, “accuracy”). Use for “ask questions on raw stats”. | `question` or `metric`: string (e.g. "mission_success_rate", "deaths", "time_played") | `outcome`, `answer` (text), `value`, `unit`, optional `data` |

Implementations can map `question`/`metric` to known fields in the statistics response so agents can ask “what’s mission success rate?” and get a single number + short answer.

---

## 4. Response Envelope (agent-friendly)

Use one envelope for all outcome and analytics tools:

```json
{
  "status": "success",
  "outcome": "ok",
  "summary": "One-line or short paragraph for the LLM.",
  "data": { ... },
  "error": null,
  "metrics": { "elapsed_ms": 12 }
}
```

For outcome tools, add outcome-specific fields at the top level (e.g. `recommendations`, `priorities`, `success_rate`) so agents don’t have to dig into `data` for common use cases. Keep `data` for raw or extended payloads so users can still “ask questions on raw stats and messages” when needed.

---

## 5. Implementation Outline

1. **Keep existing 7 tools** as the raw layer; document them as “raw API data for custom and stats questions.”
2. **Add `get_raw_api`** (optional): single entry point for raw API by `endpoint` (+ optional `planet_index`).
3. **Add analytics module** (e.g. `highcommand/analytics.py`):
   - `mission_analytics(raw_stats) -> dict`
   - `war_analytics(war_status, campaigns, planets?) -> dict`
   - `planet_analytics(planets, campaigns?) -> dict`
   - `query_stat_metric(raw_stats, metric_key) -> { answer, value, unit }`
4. **Add outcome module** (e.g. `highcommand/outcomes.py`):
   - `war_summary(war_status) -> { outcome, summary, ... }`
   - `where_to_deploy(campaigns, planets, planet_statuses?) -> { outcome, summary, recommendations }`
   - `liberation_priority(planets, campaigns?, planet_statuses?) -> { outcome, summary, priorities }`
   - `mission_efficiency_snapshot(statistics) -> { outcome, summary, success_rate, ... }`
5. **Wire in server**: Register new tools in `server.py` and implement handlers in `tools.py` (or a dedicated `outcome_tools.py` / `analytics_tools.py`) that call the API client, then analytics/outcomes, and return the standard envelope.
6. **Tool registry**: Register new tools in `ToolRegistry` with clear names and descriptions so Cursor/agents see outcome-based descriptions.

---

## 6. Summary

| Category | Role | Example tools |
|----------|------|----------------|
| **Raw** | “Ask questions on raw stats and messages” | Existing 7 tools + optional `get_raw_api` |
| **Outcome** | “What should I do?” / “What’s the outcome?” | `get_war_summary`, `get_where_to_deploy`, `get_liberation_priority`, `get_mission_efficiency_snapshot` |
| **Analytics** | “How to efficiently complete goals and missions” + stats questions | `get_mission_analytics`, `get_war_analytics`, `get_planet_analytics`, `query_stats` |

This keeps raw access for power users and agents while adding outcome-based and analytics tools that are agent-friendly and support efficient completion of goals and missions.
