from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from garmin_mcp.service import METHODS, GarminReadError, GarminService, iso_day


@pytest.mark.parametrize("day", ["2026-02-30", "20260907", "2026-W37-1", "today", ""])
def test_invalid_dates(day):
    with pytest.raises(ValueError):
        iso_day(day)


@pytest.mark.parametrize("start,limit", [(-1, 20), (0, 0), (0, 101), (True, 1), (0, 1.2)])
def test_bounded_pagination(start, limit):
    client = Mock()
    with pytest.raises(ValueError):
        GarminService(client).activities(start, limit)
    client.get_activities.assert_not_called()


def test_pagination_and_cache_do_not_mutate_upstream_data():
    client = Mock()
    client.get_activities.return_value = [{"activityId": 123}]
    service = GarminService(client)
    first = service.activities(0, 1)
    assert first["pagination"]["next_start"] == 1
    first["data"][0]["activityId"] = 999
    second = service.activities(0, 1)
    assert second["data"][0]["activityId"] == 123
    assert first["fetched_at_utc"] == second["fetched_at_utc"]
    client.get_activities.assert_called_once_with(0, 1)


def test_end_of_history():
    client = Mock()
    client.get_activities.return_value = []
    assert GarminService(client).activities()["pagination"]["next_start"] is None


def test_cache_expiry():
    now = [0]
    client = Mock()
    service = GarminService(client, clock=lambda: now[0])
    service.health("2026-09-07", "sleep")
    now[0] = 301
    service.health("2026-09-07", "sleep")
    assert client.get_sleep_data.call_count == 2


def test_concurrent_requests_share_cached_result():
    client = Mock()
    service = GarminService(client)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: service.health("2026-09-07", "sleep"), range(30)))
    client.get_sleep_data.assert_called_once()


@pytest.mark.parametrize("metric,method", METHODS.items())
def test_metric_dispatch_preserves_missing_data(metric, method):
    client = Mock()
    getattr(client, method).return_value = None
    result = GarminService(client).health("2026-09-07", metric)
    assert result["data"] is None
    assert result["date"] == "2026-09-07"
    getattr(client, method).assert_called_once_with("2026-09-07")


def test_secrets_not_exposed_in_upstream_errors():
    client = Mock()
    client.get_sleep_data.side_effect = RuntimeError("secret-token-and-health-data")
    service = GarminService(client)
    with pytest.raises(GarminReadError) as error:
        service.health("2026-09-07", "sleep")
    assert "secret-token" not in str(error.value)
    assert not service.cache


def test_activity_dispatch():
    client = Mock()
    GarminService(client).activity(123, "splits")
    client.get_activity_splits.assert_called_once_with("123")


def test_no_arbitrary_endpoint_access():
    with pytest.raises(ValueError):
        GarminService(Mock()).health("2026-09-07", "delete_activity")


def test_sdk_methods_exist():
    from garminconnect import Garmin

    for method in [
        *METHODS.values(),
        "get_activities",
        "get_activity",
        "get_activity_splits",
        "get_activity_hr_in_timezones",
    ]:
        assert callable(getattr(Garmin, method))
