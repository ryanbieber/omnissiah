#!/usr/bin/env python3
"""
Weather checking tool for lawn care decisions.
Fetches weather data and determines impact on lawn maintenance.
"""
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def weather_check(
    location: str = "Waverly, Iowa",
    days_ahead: int = 3,
    metrics: Optional[List[str]] = None
) -> Dict:
    """
    Check weather conditions relevant to lawn care.
    
    Args:
        location: Location string (default: Waverly, Iowa)
        days_ahead: Days to forecast (default: 3)
        metrics: Specific metrics to check (precipitation, temperature, humidity)
    
    Returns:
        Weather data with lawn care implications
    """
    if metrics is None:
        metrics = ["precipitation", "temperature", "humidity"]
    
    # In production, this would call a real weather API (OpenWeatherMap, WeatherAPI, etc)
    # For now, return example structure
    
    forecast = {
        "location": location,
        "timestamp": datetime.now().isoformat(),
        "forecast_days": days_ahead,
        "data": [
            {
                "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                "temperature_high_f": 72 + (i % 3),
                "temperature_low_f": 58 + (i % 3),
                "precipitation_in": 0.1 * (i % 2),  # Alternate rain/no rain
                "humidity_percent": 65 + (i * 5),
                "wind_speed_mph": 8 + (i % 3),
                "recommendation": determine_lawn_action(i)
            }
            for i in range(days_ahead)
        ]
    }
    
    return forecast


def determine_lawn_action(day_offset: int) -> str:
    """Determine lawn care action based on weather day."""
    if day_offset == 0:
        if day_offset % 2 == 0:
            return "FAVORABLE: Apply fertilizer or overseed"
        else:
            return "CAUTION: Rain expected, delay applications"
    elif day_offset == 1:
        return "MONITOR: Check conditions before watering"
    else:
        return "PLAN: Prepare for potential frost or heat stress"


if __name__ == "__main__":
    # CLI interface
    if len(sys.argv) > 1:
        location = sys.argv[1]
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        result = weather_check(location, days)
    else:
        result = weather_check()
    
    print(json.dumps(result, indent=2))
