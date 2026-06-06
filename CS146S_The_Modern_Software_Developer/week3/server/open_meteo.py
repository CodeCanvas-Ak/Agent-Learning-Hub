"""Open-Meteo API 的 HTTP 客户端辅助封装。"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx



WMO_WEATHER_CODES: dict[int, str] = {
    0: "晴朗",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴天",
    45: "起雾",
    48: "结霜雾",
    51: "小雨毛",
    53: "中雨毛",
    55: "大雨毛",
    56: "轻度冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "轻度冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "中阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}


class ExternalAPIError(RuntimeError):
    """当上游 API 请求失败时抛出。"""


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


class OpenMeteoClient:
    """对 Open-Meteo API 的一个轻量且更稳健的封装。"""

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self) -> None:
        timeout_seconds = _env_float("OPEN_METEO_TIMEOUT_SECONDS", 10.0)
        self.max_retries = _env_int("OPEN_METEO_MAX_RETRIES", 2)
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "User-Agent": os.getenv(
                    "WEATHER_MCP_USER_AGENT",
                    "openmeteo-mcp-local/0.1.0 (course-assignment)",
                )
            },
        )

    def close(self) -> None:
        self.client.close()

    def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        delay_seconds = 1.0

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(url, params=params)

                if response.status_code == 429:
                    if attempt >= self.max_retries:
                        raise ExternalAPIError(
                            "Open-Meteo 接口访问超限，请稍后重试。"
                        )

                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        time.sleep(float(retry_after))
                    else:
                        time.sleep(delay_seconds)
                        delay_seconds *= 2
                    continue

                response.raise_for_status()
                try:
                    return response.json()
                except ValueError as exc:
                    raise ExternalAPIError(
                        "Open-Meteo 返回的数据格式异常，非标准JSON。"
                    ) from exc

            except httpx.TimeoutException as exc:
                if attempt >= self.max_retries:
                    raise ExternalAPIError(
                        "请求天气接口超时，已用尽重试次数。"
                    ) from exc
                time.sleep(delay_seconds)
                delay_seconds *= 2

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if 500 <= status_code < 600 and attempt < self.max_retries:
                    time.sleep(delay_seconds)
                    delay_seconds *= 2
                    continue

                raise ExternalAPIError(
                    f"天气接口访问异常，错误码：HTTP {status_code}"
                ) from exc

            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise ExternalAPIError(
                        "网络异常，无法连接Open-Meteo天气服务器。"
                    ) from exc
                time.sleep(delay_seconds)
                delay_seconds *= 2

        raise ExternalAPIError("天气接口请求发生未知异常。")

    def search_locations(
        self,
        query: str,
        *,
        count: int = 5,
        language: str = "en",
        country_code: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "name": query,
            "count": count,
            "language": language,
            "format": "json",
        }
        if country_code:
            params["countryCode"] = country_code

        payload = self._request_json(self.GEOCODING_URL, params)
        results = payload.get("results") or []

        mapped_results = [
            {
                "name": item.get("name"),
                "country": item.get("country"),
                "country_code": item.get("country_code"),
                "admin1": item.get("admin1"),
                "admin2": item.get("admin2"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "elevation_m": item.get("elevation"),
                "population": item.get("population"),
                "timezone": item.get("timezone"),
            }
            for item in results
        ]

        if not mapped_results:
            return {
                "query": query,
                "results": [],
                "message": f"未查询到【{query}】匹配的地点。",
            }

        return {
            "query": query,
            "results": mapped_results,
            "message": f"成功找到 {len(mapped_results)} 个匹配地点。",
        }

    def get_current_weather(
        self,
        *,
        latitude: float,
        longitude: float,
        timezone: str = "auto",
        temperature_unit: str = "celsius",
        wind_speed_unit: str = "kmh",
        precipitation_unit: str = "mm",
    ) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "temperature_unit": temperature_unit,
            "wind_speed_unit": wind_speed_unit,
            "precipitation_unit": precipitation_unit,
            "current": ",".join(
                [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "is_day",
                    "precipitation",
                    "rain",
                    "showers",
                    "snowfall",
                    "weather_code",
                    "cloud_cover",
                    "wind_speed_10m",
                    "wind_direction_10m",
                ]
            ),
        }

        payload = self._request_json(self.FORECAST_URL, params)
        current = payload.get("current")
        units = payload.get("current_units", {})

        if not current:
            raise ExternalAPIError("Open-Meteo 未返回实时天气数据。")

        weather_code = current.get("weather_code")
        return {
            "coordinates": {
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
            },
            "timezone": payload.get("timezone"),
            "timezone_abbreviation": payload.get("timezone_abbreviation"),
            "elevation_m": payload.get("elevation"),
            "current": {
                "time": current.get("time"),
                "weather_code": weather_code,
                "weather_description": WMO_WEATHER_CODES.get(
                    weather_code, "未知天气类型"
                ),
                "temperature": {
                    "value": current.get("temperature_2m"),
                    "unit": units.get("temperature_2m"),
                },
                "apparent_temperature": {
                    "value": current.get("apparent_temperature"),
                    "unit": units.get("apparent_temperature"),
                },
                "humidity": {
                    "value": current.get("relative_humidity_2m"),
                    "unit": units.get("relative_humidity_2m"),
                },
                "precipitation": {
                    "value": current.get("precipitation"),
                    "unit": units.get("precipitation"),
                },
                "wind_speed": {
                    "value": current.get("wind_speed_10m"),
                    "unit": units.get("wind_speed_10m"),
                },
                "wind_direction_degrees": current.get("wind_direction_10m"),
                "cloud_cover": {
                    "value": current.get("cloud_cover"),
                    "unit": units.get("cloud_cover"),
                },
                "is_day": bool(current.get("is_day")),
            },
        }

    def get_daily_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        days: int = 3,
        timezone: str = "auto",
        temperature_unit: str = "celsius",
        wind_speed_unit: str = "kmh",
        precipitation_unit: str = "mm",
    ) -> dict[str, Any]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": days,
            "temperature_unit": temperature_unit,
            "wind_speed_unit": wind_speed_unit,
            "precipitation_unit": precipitation_unit,
            "daily": ",".join(
                [
                    "weather_code",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "wind_speed_10m_max",
                    "sunrise",
                    "sunset",
                ]
            ),
        }

        payload = self._request_json(self.FORECAST_URL, params)
        daily = payload.get("daily")
        units = payload.get("daily_units", {})

        if not daily or not daily.get("time"):
            raise ExternalAPIError("Open-Meteo 未返回逐日预报数据。")

        entries: list[dict[str, Any]] = []
        for index, date_value in enumerate(daily["time"]):
            weather_code = daily["weather_code"][index]
            entries.append(
                {
                    "date": date_value,
                    "weather_code": weather_code,
                    "weather_description": WMO_WEATHER_CODES.get(
                        weather_code, "未知天气类型"
                    ),
                    "temperature_max": {
                        "value": daily["temperature_2m_max"][index],
                        "unit": units.get("temperature_2m_max"),
                    },
                    "temperature_min": {
                        "value": daily["temperature_2m_min"][index],
                        "unit": units.get("temperature_2m_min"),
                    },
                    "precipitation_sum": {
                        "value": daily["precipitation_sum"][index],
                        "unit": units.get("precipitation_sum"),
                    },
                    "precipitation_probability_max": {
                        "value": daily["precipitation_probability_max"][index],
                        "unit": units.get("precipitation_probability_max"),
                    },
                    "wind_speed_max": {
                        "value": daily["wind_speed_10m_max"][index],
                        "unit": units.get("wind_speed_10m_max"),
                    },
                    "sunrise": daily["sunrise"][index],
                    "sunset": daily["sunset"][index],
                }
            )

        return {
            "coordinates": {
                "latitude": payload.get("latitude"),
                "longitude": payload.get("longitude"),
            },
            "timezone": payload.get("timezone"),
            "timezone_abbreviation": payload.get("timezone_abbreviation"),
            "forecast_days": days,
            "daily": entries,
        }