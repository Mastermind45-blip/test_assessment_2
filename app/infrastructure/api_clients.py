"""Async API clients for external services (weather, YouTube, Google Maps, etc.)."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """Async client for weather API (e.g., OpenWeatherMap)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openweather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_forecast(
        self, lat: float, lon: float, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get weather forecast for coordinates.

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days (max 7 for free tier)

        Returns:
            List of daily forecast data
        """
        try:
            # Using 5-day/3-hour forecast endpoint (free tier)
            # For daily forecast, we aggregate 3-hour data
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Process and aggregate forecast data by day
            daily_forecasts = self._aggregate_forecast_by_day(data)
            return daily_forecasts[:days]

        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            raise

    def _aggregate_forecast_by_day(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate 3-hour forecast data into daily forecasts."""
        from datetime import datetime

        daily_data = {}

        for item in data.get("list", []):
            # Extract date from dt_txt
            dt = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")

            if date_str not in daily_data:
                daily_data[date_str] = {
                    "forecast_date": date_str,
                    "temperatures": [],
                    "feels_like": [],
                    "humidity": [],
                    "pressure": [],
                    "wind_speed": [],
                    "descriptions": [],
                    "icons": [],
                }

            main = item.get("main", {})
            daily_data[date_str]["temperatures"].append(main.get("temp", 0))
            daily_data[date_str]["feels_like"].append(main.get("feels_like", 0))
            daily_data[date_str]["humidity"].append(main.get("humidity", 0))
            daily_data[date_str]["pressure"].append(main.get("pressure", 0))
            daily_data[date_str]["wind_speed"].append(
                item.get("wind", {}).get("speed", 0)
            )

            weather = item.get("weather", [{}])[0]
            daily_data[date_str]["descriptions"].append(weather.get("description", ""))
            daily_data[date_str]["icons"].append(weather.get("icon", ""))

        # Calculate daily aggregates
        result = []
        for date_str, day_data in daily_data.items():
            result.append(
                {
                    "forecast_date": date_str,
                    "temperature": (
                        sum(day_data["temperatures"]) / len(day_data["temperatures"])
                        if day_data["temperatures"]
                        else None
                    ),
                    "feels_like": (
                        sum(day_data["feels_like"]) / len(day_data["feels_like"])
                        if day_data["feels_like"]
                        else None
                    ),
                    "temp_min": (
                        min(day_data["temperatures"])
                        if day_data["temperatures"]
                        else None
                    ),
                    "temp_max": (
                        max(day_data["temperatures"])
                        if day_data["temperatures"]
                        else None
                    ),
                    "humidity": (
                        int(sum(day_data["humidity"]) / len(day_data["humidity"]))
                        if day_data["humidity"]
                        else None
                    ),
                    "pressure": (
                        int(sum(day_data["pressure"]) / len(day_data["pressure"]))
                        if day_data["pressure"]
                        else None
                    ),
                    "wind_speed": (
                        sum(day_data["wind_speed"]) / len(day_data["wind_speed"])
                        if day_data["wind_speed"]
                        else None
                    ),
                    "weather_description": (
                        max(
                            set(day_data["descriptions"]),
                            key=day_data["descriptions"].count,
                        )
                        if day_data["descriptions"]
                        else None
                    ),
                    "icon_code": (
                        max(set(day_data["icons"]), key=day_data["icons"].count)
                        if day_data["icons"]
                        else None
                    ),
                }
            )

        return sorted(result, key=lambda x: x["forecast_date"])


class YouTubeAPIClient:
    """Async client for YouTube Data API."""

    def __init__(self, api_key: Optional[str] = None):
        # Note: YouTube API key not in config yet, using placeholder
        self.api_key = api_key or getattr(settings, "youtube_api_key", "")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_videos(
        self, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search YouTube videos related to a location/weather.

        Args:
            query: Search query (e.g., "weather in London")
            max_results: Maximum number of results to return

        Returns:
            List of video data dictionaries
        """
        try:
            url = f"{self.base_url}/search"
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "key": self.api_key,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                videos.append(
                    {
                        "video_id": item.get("id", {}).get("videoId", ""),
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "url": f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId', '')}",
                        "thumbnail_url": snippet.get("thumbnails", {})
                        .get("default", {})
                        .get("url", ""),
                        "channel_title": snippet.get("channelTitle", ""),
                        "published_at": snippet.get("publishedAt", ""),
                    }
                )

            return videos

        except httpx.HTTPStatusError as e:
            logger.error(f"YouTube API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise


class GoogleMapsClient:
    """Async client for Google Maps API."""

    def __init__(self, api_key: Optional[str] = None):
        # Note: Google Maps API key not in config yet, using placeholder
        self.api_key = api_key or getattr(settings, "google_maps_api_key", "")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_place_details(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get place details from coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with place information
        """
        try:
            # First, reverse geocode to get address
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "latlng": f"{lat},{lon}",
                "key": self.api_key,
            }

            response = await self.client.get(geocode_url, params=params)
            response.raise_for_status()
            geocode_data = response.json()

            if geocode_data.get("status") != "OK":
                return {}

            result = geocode_data.get("results", [{}])[0]

            return {
                "place_id": result.get("place_id", ""),
                "formatted_address": result.get("formatted_address", ""),
                "map_url": f"https://www.google.com/maps?q={lat},{lon}",
                "static_map_url": f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lon}&zoom=12&size=400x400&key={self.api_key}",
                "lat": lat,
                "lng": lon,
                "place_type": ",".join(result.get("types", [])[:3]),  # First 3 types
                "point_of_interest": result.get("name", ""),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Google Maps API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Google Maps API error: {str(e)}")
            raise


class APIClientManager:
    """Manager to handle all API clients with context manager support."""

    def __init__(self):
        self.weather_client = WeatherAPIClient()
        self.youtube_client = YouTubeAPIClient()
        self.maps_client = GoogleMapsClient()

    async def close_all(self):
        """Close all API clients."""
        await asyncio.gather(
            self.weather_client.close(),
            self.youtube_client.close(),
            self.maps_client.close(),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all()
