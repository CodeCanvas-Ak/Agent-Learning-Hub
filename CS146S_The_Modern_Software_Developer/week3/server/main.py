"""基于 Open-Meteo 的本地 STDIO MCP 天气服务。"""

from __future__ import annotations

import atexit
import logging
import sys
from typing import Literal

from mcp.server.fastmcp import FastMCP

from server.open_meteo import ExternalAPIError, OpenMeteoClient


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

mcp = FastMCP(
    "OpenMeteo Local Weather",
    instructions=(
        "使用此服务可以搜索地点，并从 Open-Meteo 获取当前天气和逐日天气预报。"
        "如果你还不知道经纬度，建议先调用地点搜索工具。"
    ),
)
client = OpenMeteoClient()
atexit.register(client.close)

TemperatureUnit = Literal["celsius", "fahrenheit"]
WindSpeedUnit = Literal["kmh", "ms", "mph", "kn"]
PrecipitationUnit = Literal["mm", "inch"]


def _validate_query(query: str) -> str:
    clean_query = query.strip()
    if len(clean_query) < 2:
        raise ValueError("`query` must contain at least 2 characters.")
    return clean_query


def _validate_country_code(country_code: str | None) -> str | None:
    if country_code is None:
        return None
    clean_code = country_code.strip().upper()
    if len(clean_code) != 2 or not clean_code.isalpha():
        raise ValueError("`country_code` must be a 2-letter ISO country code.")
    return clean_code


def _validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    if not -90 <= latitude <= 90:
        raise ValueError("`latitude` must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("`longitude` must be between -180 and 180.")
    return latitude, longitude


def _validate_limit(limit: int) -> int:
    if not 1 <= limit <= 10:
        raise ValueError("`limit` must be between 1 and 10.")
    return limit


def _validate_days(days: int) -> int:
    if not 1 <= days <= 16:
        raise ValueError("`days` must be between 1 and 16.")
    return days


@mcp.tool()
def search_locations(
    query: str,
    country_code: str | None = None,
    limit: int = 5,
    language: str = "en",
) -> dict:
    """使用 Open-Meteo 地理编码 API 搜索城市或地区。

    Args:
        query: 地点关键词，例如 "Tokyo"、"Berlin" 或 "San Francisco"。
        country_code: 可选的 2 位 ISO 国家代码，用于缩小搜索范围。
        limit: 返回的最大结果数，取值范围为 1 到 10。
        language: Open-Meteo 支持的结果语言代码，默认值为 "en"。
    """
    clean_query = _validate_query(query)
    clean_country_code = _validate_country_code(country_code)
    clean_limit = _validate_limit(limit)

    try:
        result = client.search_locations(
            clean_query,
            count=clean_limit,
            language=language.strip() or "en",
            country_code=clean_country_code,
        )
        logger.info("search_locations query=%s limit=%s", clean_query, clean_limit)
        return result
    except ExternalAPIError:
        logger.exception("search_locations failed")
        raise


@mcp.tool()
def get_current_weather(
    latitude: float,
    longitude: float,
    timezone: str = "auto",
    temperature_unit: TemperatureUnit = "celsius",
    wind_speed_unit: WindSpeedUnit = "kmh",
    precipitation_unit: PrecipitationUnit = "mm",
) -> dict:
    """根据经纬度获取当前天气情况。

    Args:
        latitude: 十进制纬度，范围 -90 到 90。
        longitude: 十进制经度，范围 -180 到 180。
        timezone: IANA 时区名称，或使用 "auto" 让 API 自动处理。
        temperature_unit: 温度单位，可选 "celsius" 或 "fahrenheit"。
        wind_speed_unit: Open-Meteo 支持的风速单位。
        precipitation_unit: 降水单位，可选 "mm" 或 "inch"。
    """
    _validate_coordinates(latitude, longitude)

    try:
        result = client.get_current_weather(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone.strip() or "auto",
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
            precipitation_unit=precipitation_unit,
        )
        logger.info("get_current_weather lat=%s lon=%s", latitude, longitude)
        return result
    except ExternalAPIError:
        logger.exception("get_current_weather failed")
        raise


@mcp.tool()
def get_daily_forecast(
    latitude: float,
    longitude: float,
    days: int = 3,
    timezone: str = "auto",
    temperature_unit: TemperatureUnit = "celsius",
    wind_speed_unit: WindSpeedUnit = "kmh",
    precipitation_unit: PrecipitationUnit = "mm",
) -> dict:
    """根据经纬度获取多日天气预报。

    Args:
        latitude: 十进制纬度，范围 -90 到 90。
        longitude: 十进制经度，范围 -180 到 180。
        days: 返回的预报天数，范围 1 到 16。
        timezone: IANA 时区名称，或使用 "auto" 让 API 自动处理。
        temperature_unit: 温度单位，可选 "celsius" 或 "fahrenheit"。
        wind_speed_unit: Open-Meteo 支持的风速单位。
        precipitation_unit: 降水单位，可选 "mm" 或 "inch"。
    """
    _validate_coordinates(latitude, longitude)
    clean_days = _validate_days(days)

    try:
        result = client.get_daily_forecast(
            latitude=latitude,
            longitude=longitude,
            days=clean_days,
            timezone=timezone.strip() or "auto",
            temperature_unit=temperature_unit,
            wind_speed_unit=wind_speed_unit,
            precipitation_unit=precipitation_unit,
        )
        logger.info(
            "get_daily_forecast lat=%s lon=%s days=%s",
            latitude,
            longitude,
            clean_days,
        )
        return result
    except ExternalAPIError:
        logger.exception("get_daily_forecast failed")
        raise


@mcp.resource("weather://service-info")
def service_info() -> str:
    """描述上游接口与服务行为。"""
    return (
        "# OpenMeteo 本地天气 MCP 服务\n\n"
        "- 部署方式：本地 STDIO 服务\n"
        "- 上游 API 1：https://geocoding-api.open-meteo.com/v1/search\n"
        "- 上游 API 2：https://api.open-meteo.com/v1/forecast\n"
        "- 工具：search_locations、get_current_weather、get_daily_forecast\n"
        "- 健壮性：超时处理、指数退避重试、429 限流提示、空结果友好返回\n"
    )


@mcp.prompt()
def weather_briefing(location: str, focus: str = "travel") -> str:
    """将天气工具输出整理为简明简报的提示词模板。"""
    return (
        f"你正在为 {location} 准备一份天气简报。"
        f"重点关注 {focus}。请先调用天气 MCP 工具，获取最匹配的地点、"
        "当前天气情况以及简短的多日预报，然后总结主要风险、温度趋势、"
        "降水情况以及实际建议。"
    )


def main() -> None:
    """通过 STDIO 运行 MCP 服务。"""
    mcp.run()


if __name__ == "__main__":
    main()
