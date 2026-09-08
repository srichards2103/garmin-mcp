"""Bounded, serialized Garmin reads. No credentials or persistent health cache."""

from collections import OrderedDict
from copy import deepcopy
from datetime import UTC, date, datetime
from threading import RLock
from time import monotonic
from typing import Any


class GarminReadError(Exception):
    """An intentionally sanitized error safe to show to an MCP client."""


METHODS = {
    "summary": "get_user_summary",
    "heart_rate": "get_heart_rates",
    "sleep": "get_sleep_data",
    "hrv": "get_hrv_data",
    "stress": "get_stress_data",
    "body_battery": "get_body_battery",
    "training_readiness": "get_training_readiness",
    "training_status": "get_training_status",
}


def iso_day(value: str) -> str:
    try:
        result = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("Use a valid date in YYYY-MM-DD format.") from None
    if result.isoformat() != value:
        raise ValueError("Use a valid date in YYYY-MM-DD format.")
    return value


class GarminService:
    def __init__(self, client: Any, ttl: float = 300, clock=monotonic):
        self.client = client
        self.ttl = ttl
        self.clock = clock
        self.cache: OrderedDict = OrderedDict()
        self.lock = RLock()

    def _read(self, method: str, *args: Any) -> dict:
        key = (method, *args)
        with self.lock:
            cached = self.cache.get(key)
            if cached and self.clock() - cached[0] < self.ttl:
                self.cache.move_to_end(key)
                return deepcopy(cached[1])
            try:
                data = getattr(self.client, method)(*args)
            except Exception as exc:
                kind = type(exc).__name__
                if "TooManyRequests" in kind:
                    message = "Garmin rate limited this request. Wait before retrying."
                elif "Authentication" in kind:
                    message = "Garmin session expired. Run garmin-mcp login locally."
                else:
                    message = (
                        "Garmin could not provide this data. The metric may be unavailable "
                        "for this device/account, or Garmin may be temporarily unavailable."
                    )
                raise GarminReadError(message) from None
            result = {
                "source": "Garmin Connect (unofficial API)",
                "fetched_at_utc": datetime.now(UTC).isoformat(),
                "data": data,
            }
            self.cache[key] = (self.clock(), deepcopy(result))
            self.cache.move_to_end(key)
            while len(self.cache) > 128:
                self.cache.popitem(last=False)
            return result

    def activities(self, start: int = 0, limit: int = 20) -> dict:
        if isinstance(start, bool) or not isinstance(start, int) or not 0 <= start <= 10000:
            raise ValueError("start must be an integer between 0 and 10000.")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer between 1 and 100.")
        result = self._read("get_activities", start, limit)
        result["pagination"] = {
            "start": start,
            "limit": limit,
            "next_start": start + limit if len(result["data"]) == limit else None,
        }
        return result

    def activity(self, activity_id: int, section: str = "summary") -> dict:
        if isinstance(activity_id, bool) or not isinstance(activity_id, int) or activity_id <= 0:
            raise ValueError("activity_id must be a positive integer.")
        methods = {
            "summary": "get_activity",
            "splits": "get_activity_splits",
            "heart_rate_zones": "get_activity_hr_in_timezones",
        }
        if section not in methods:
            raise ValueError("section must be summary, splits, or heart_rate_zones.")
        return self._read(methods[section], str(activity_id))

    def health(self, day: str, metric: str) -> dict:
        iso_day(day)
        if metric not in METHODS:
            raise ValueError("Unknown health metric.")
        result = self._read(METHODS[metric], day)
        result["date"] = day
        result["metric"] = metric
        return result
