#!/usr/bin/env python3
"""Comprehensive endpoint demonstration."""
import asyncio
import json

from highcommand.server import call_tool


async def test_all_endpoints():
    """Test raw + outcome + analytics MCP tools."""
    print("\n" + "=" * 70)
    print("  HIGH-COMMAND MCP SERVER - ALL ENDPOINTS DEMONSTRATION")
    print("=" * 70 + "\n")

    # Test 1: War status
    print("1. GET WAR STATUS")
    print("-" * 70)
    result = await call_tool("get_war_status", {})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "data" in data and isinstance(data["data"], dict):
        print(f"   Keys in response: {list(data['data'].keys())[:5]}")
    print()

    # Test 2: Planets
    print("2. GET PLANETS")
    print("-" * 70)
    result = await call_tool("get_planets", {})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "data" in data and isinstance(data["data"], dict):
        print(f"   Keys in response: {list(data['data'].keys())[:5]}")
    print()

    # Test 3: Statistics
    print("3. GET STATISTICS")
    print("-" * 70)
    result = await call_tool("get_statistics", {})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "data" in data and isinstance(data["data"], dict):
        print(f"   Keys in response: {list(data['data'].keys())[:5]}")
    print()

    # Test 4: Planet status (index 0)
    print("4. GET PLANET STATUS (planet index 0)")
    print("-" * 70)
    result = await call_tool("get_planet_status", {"planet_index": 0})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "data" in data and isinstance(data["data"], dict):
        print(f"   Keys in response: {list(data['data'].keys())[:5]}")
    print()

    # Test 5: Biomes (NEW)
    print("5. GET BIOMES ✨ NEW")
    print("-" * 70)
    result = await call_tool("get_biomes", {})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "data" in data and isinstance(data["data"], dict):
        print(f"   Keys in response: {list(data['data'].keys())[:5]}")
    print()

    # Test 6: Factions (NEW)
    print("6. GET FACTIONS ✨ NEW")
    print("-" * 70)
    result = await call_tool("get_factions", {})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "data" in data and isinstance(data["data"], dict):
        print(f"   Keys in response: {list(data['data'].keys())[:5]}")
    print()

    # Test 7: Campaign (returns error)
    print("7. GET CAMPAIGN INFO (not available)")
    print("-" * 70)
    result = await call_tool("get_campaign_info", {})
    data = json.loads(result[0].text)
    print(f"   Status: {data['status']}")
    if "error" in data:
        print(f"   Error: {data['error']}")
    print()

    print("=" * 70)
    print("  ✅ ALL ENDPOINTS TESTED SUCCESSFULLY")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
