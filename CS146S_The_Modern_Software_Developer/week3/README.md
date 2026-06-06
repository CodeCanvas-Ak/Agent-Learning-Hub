# OpenMeteo 本地天气 MCP 服务

这是一个基于官方 Python MCP SDK 实现的本地 STDIO MCP 服务。它封装了真实的 Open-Meteo API，为 Claude Desktop 等支持 MCP 的客户端提供地点搜索、当前天气查询和多日天气预报能力。

## 为什么这个项目符合本次作业要求

- 使用了真实外部 API：Open-Meteo 地理编码 API 与天气预报 API
- 提供了 3 个 MCP 工具，超过作业要求的至少 2 个工具
- 采用本地 STDIO 方式运行
- 实现了输入校验、超时处理、重试/退避与限流处理
- 额外提供了 1 个 MCP resource 和 1 个 MCP prompt，不止停留在最基础的 tool 实现

## 外部 API 与端点说明

本服务使用了两个 Open-Meteo 接口：

1. 地理编码搜索
   - `GET https://geocoding-api.open-meteo.com/v1/search`
   - 用途：将城市名或地区名转换为经纬度
2. 天气预报数据
   - `GET https://api.open-meteo.com/v1/forecast`
   - 用途：获取当前天气与多日天气预报

## 项目结构

```text
week3/
├─ server/
│  ├─ __init__.py
│  ├─ main.py
│  └─ open_meteo.py
├─ .env.example
├─ pyproject.toml
└─ README.md
```

## 运行前准备

- Python 3.11 或更高版本
- 可访问互联网，以便调用 Open-Meteo API
- 一个支持 MCP 的客户端，例如 Claude Desktop

## 安装与配置

强烈建议使用独立虚拟环境，避免 MCP SDK 影响你电脑上其他 Python 项目的依赖环境。

### 1. 创建并激活虚拟环境

Windows PowerShell：

```powershell
cd c:\Users\ankar\Desktop\146s\modern-software-dev-assignments\week3
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
pip install -e .
```

### 3. 可选环境变量

如果你想调整运行时行为，可以将 `.env.example` 中的值复制到你的 shell 环境或本地环境管理工具中。

可用变量如下：

- `OPEN_METEO_TIMEOUT_SECONDS`
  - 默认值：`10`
  - 控制上游 HTTP 请求超时时间
- `OPEN_METEO_MAX_RETRIES`
  - 默认值：`2`
  - 控制超时、瞬时网络错误、HTTP 429 和 HTTP 5xx 的重试次数
- `WEATHER_MCP_USER_AGENT`
  - 默认值：`openmeteo-mcp-local/0.1.0 (course-assignment)`
  - 作为 HTTP 请求头发送给上游服务

示例：

```powershell
$env:OPEN_METEO_TIMEOUT_SECONDS="10"
$env:OPEN_METEO_MAX_RETRIES="2"
```

## 本地运行 MCP 服务

在 `week3` 目录下执行：

```powershell
python -m server.main
```

或者在执行 `pip install -e .` 之后，使用脚本入口：

```powershell
openmeteo-mcp
```

这是一个本地 STDIO 服务。启动后它会等待 MCP 客户端连接，不会像普通命令行程序那样显示交互界面。

## Claude Desktop 本地配置示例

在 Claude Desktop 的 MCP 配置中加入如下服务项。在 Windows 环境中，通常可以写成这样：

```json
{
  "mcpServers": {
    "openmeteo-local-weather": {
      "command": "c:\\Users\\ankar\\Desktop\\146s\\modern-software-dev-assignments\\week3\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "server.main"
      ],
      "cwd": "c:\\Users\\ankar\\Desktop\\146s\\modern-software-dev-assignments\\week3",
      "env": {
        "OPEN_METEO_TIMEOUT_SECONDS": "10",
        "OPEN_METEO_MAX_RETRIES": "2"
      }
    }
  }
}
```

如果你使用的是全局 Python 或其他路径，请相应修改 `command` 字段。

## 示例调用流程

示例 1：

1. 在 Claude Desktop 中输入：`Search for Berlin and give me today's weather plus a 3-day forecast.`
2. 模型可以先调用 `search_locations`，例如：
   - `query = "Berlin"`
   - `limit = 5`
3. 从返回结果中选择正确的经纬度。
4. 然后调用：
   - `get_current_weather`
   - `get_daily_forecast`
5. 最终返回当前天气与未来几天的预报摘要。

示例 2：

1. 输入：`Plan a short weather briefing for Kyoto focused on travel.`
2. 模型可以结合 `weather_briefing` prompt 模板和天气工具生成结果。

## 工具说明

### `search_locations`

使用 Open-Meteo 地理编码 API 搜索城市或地区。

参数：

- `query: str`
  - 必填
  - 至少 2 个字符
- `country_code: str | None`
  - 可选
  - 2 位 ISO 国家代码，例如 `JP`、`DE`
- `limit: int`
  - 可选
  - 默认值 `5`
  - 合法范围：`1..10`
- `language: str`
  - 可选
  - 默认值 `en`

示例输入：

```json
{
  "query": "Tokyo",
  "country_code": "JP",
  "limit": 3
}
```

示例输出结构：

```json
{
  "query": "Tokyo",
  "results": [
    {
      "name": "Tokyo",
      "country": "Japan",
      "country_code": "JP",
      "admin1": "Tokyo",
      "latitude": 35.6895,
      "longitude": 139.69171,
      "timezone": "Asia/Tokyo"
    }
  ],
  "message": "Found 1 matching location(s)."
}
```

预期行为：

- 当没有匹配结果时，返回友好的空结果结构
- 对 `query`、`country_code` 与 `limit` 做输入校验

### `get_current_weather`

根据已知经纬度获取当前天气情况。

参数：

- `latitude: float`
  - 必填
  - 范围：`-90..90`
- `longitude: float`
  - 必填
  - 范围：`-180..180`
- `timezone: str`
  - 可选
  - 默认值 `auto`
- `temperature_unit: "celsius" | "fahrenheit"`
  - 可选
  - 默认值 `celsius`
- `wind_speed_unit: "kmh" | "ms" | "mph" | "kn"`
  - 可选
  - 默认值 `kmh`
- `precipitation_unit: "mm" | "inch"`
  - 可选
  - 默认值 `mm`

示例输入：

```json
{
  "latitude": 35.6895,
  "longitude": 139.69171,
  "temperature_unit": "celsius"
}
```

示例输出结构：

```json
{
  "coordinates": {
    "latitude": 35.7,
    "longitude": 139.69
  },
  "timezone": "Asia/Tokyo",
  "current": {
    "time": "2026-06-06T15:00",
    "weather_description": "Partly cloudy",
    "temperature": {
      "value": 24.3,
      "unit": "°C"
    }
  }
}
```

预期行为：

- 返回结构化、字段统一的当前天气信息
- 当上游请求失败时，返回清晰的用户可理解错误

### `get_daily_forecast`

根据已知经纬度获取逐日天气预报。

参数：

- `latitude: float`
  - 必填
  - 范围：`-90..90`
- `longitude: float`
  - 必填
  - 范围：`-180..180`
- `days: int`
  - 可选
  - 默认值 `3`
  - 合法范围：`1..16`
- `timezone: str`
  - 可选
  - 默认值 `auto`
- `temperature_unit: "celsius" | "fahrenheit"`
  - 可选
  - 默认值 `celsius`
- `wind_speed_unit: "kmh" | "ms" | "mph" | "kn"`
  - 可选
  - 默认值 `kmh`
- `precipitation_unit: "mm" | "inch"`
  - 可选
  - 默认值 `mm`

示例输入：

```json
{
  "latitude": 52.52,
  "longitude": 13.405,
  "days": 3
}
```

示例输出结构：

```json
{
  "forecast_days": 3,
  "daily": [
    {
      "date": "2026-06-06",
      "weather_description": "Clear sky",
      "temperature_max": {
        "value": 27.4,
        "unit": "°C"
      },
      "temperature_min": {
        "value": 15.2,
        "unit": "°C"
      }
    }
  ]
}
```

预期行为：

- 每一天返回一个统一结构的预报对象
- 对经纬度和 `days` 参数做校验

## 额外 MCP 能力

除了作业最低要求之外，本项目还包含：

- Resource：`weather://service-info`
  - 用于描述上游接口和服务运行行为
- Prompt：`weather_briefing(location, focus="travel")`
  - 帮助客户端在调用天气工具后生成结构化天气简报

## 可靠性与健壮性

本服务实现了以下可靠性措施：

- 对文本、经纬度、国家代码和预报天数进行输入校验
- 支持可配置的 HTTP 超时处理
- 对以下情况使用指数退避重试：
  - HTTP `429` 限流
  - HTTP `5xx` 服务端错误
  - 瞬时网络错误
  - 请求超时
- 对地点搜索无结果时返回友好响应
- 日志输出到 `stderr` 而非 `stdout`，避免破坏 STDIO MCP 通信

## 说明与限制

- Open-Meteo 的这两个接口不需要 API Key，因此本地作业版本无需额外认证流程
- 由于这是本地 STDIO 服务，必须由支持 MCP 的客户端来启动或连接
- 天气数据来自实时上游接口，因此结果会随时间变化

## 建议演示提示词

你可以在 MCP 客户端中尝试这些提示词：

- `Find the best match for Paris, then show current weather and a 4-day forecast.`
- `Search for Seoul in Korean time and summarize rain risk for the next 3 days.`
- `Use the weather_briefing prompt for Vancouver with a hiking focus.`
