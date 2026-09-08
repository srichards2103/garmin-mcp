from unittest.mock import Mock

from fastmcp import Client

from garmin_mcp.server import create_server
from garmin_mcp.service import GarminService


async def test_protocol_discovery_and_tool_call():
    upstream = Mock()
    upstream.get_activities.return_value = [{"activityId": 123, "distance": 5000}]
    async with Client(create_server(GarminService(upstream))) as client:
        tools = await client.list_tools()
        assert {tool.name for tool in tools} == {
            "list_activities",
            "get_activity",
            "get_daily_health",
        }
        assert all(tool.annotations.read_only_hint for tool in tools)
        result = await client.call_tool("list_activities", {"limit": 1})
        assert result.data["data"][0]["activityId"] == 123
        assert result.data["pagination"]["next_start"] == 1


async def test_invalid_metric_rejected_before_garmin_call():
    upstream = Mock()
    async with Client(create_server(GarminService(upstream))) as client:
        result = await client.call_tool(
            "get_daily_health",
            {"day": "2026-09-07", "metric": "delete_activity"},
            raise_on_error=False,
        )
        assert result.is_error
        assert not upstream.mock_calls
