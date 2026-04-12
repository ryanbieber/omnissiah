#!/usr/bin/env python3
"""
Watering decision tool for lawn care.
Determines if lawn needs watering based on weather, soil, and recent precipitation.
"""
import json
import sys
from typing import Dict, Optional


def watering_decision(
    lawn_size_sqft: int,
    soil_type: str = "loam",
    weather_data: Optional[Dict] = None,
    last_watered_hours: int = 72,
    last_rainfall_inches: float = 0.0,
    last_rainfall_hours: int = 96
) -> Dict:
    """
    Make smart watering decision based on multiple factors.
    
    Args:
        lawn_size_sqft: Size of lawn
        soil_type: Type of soil (clay, loam, sand)
        weather_data: Recent/forecast weather data
        last_watered_hours: Hours since last watering
        last_rainfall_inches: Recent rainfall amount
        last_rainfall_hours: Hours since last rain
    
    Returns:
        Watering recommendation with reasoning
    """
    
    # Soil water retention by type (days between watering)
    soil_retention = {
        "clay": 5,        # Holds water longer
        "loam": 3,        # Moderate retention
        "sand": 1.5       # Drains quickly
    }
    
    days_since_watered = last_watered_hours / 24
    days_since_rain = last_rainfall_hours / 24
    retention = soil_retention.get(soil_type, 3)
    
    # Determine if watering needed
    needs_water = False
    reason = ""
    
    if days_since_watered > retention:
        needs_water = True
        reason = f"Soil type {soil_type} retains water {retention} days. Last watered {days_since_watered:.1f} days ago."
    
    if last_rainfall_inches > 0.5 and days_since_rain < 2:
        needs_water = False
        reason = f"Received {last_rainfall_inches}\" of rain {days_since_rain:.1f} days ago. Skip watering."
    
    if not reason:
        reason = f"Soil type {soil_type}, last watered {days_since_watered:.1f} days ago."
    
    # Calculate watering recommendations
    # Cool-season grass: 1-1.5 inches per week
    weekly_requirement = 1.25  # inches
    days_to_next_watering = retention
    
    # Account for recent rainfall
    if last_rainfall_inches > 0:
        weekly_requirement = max(0, weekly_requirement - last_rainfall_inches)
    
    # Daily rate if spreading over multiple days
    daily_watering = weekly_requirement / 7
    
    recommendation = {
        "decision": "WATER NOW" if needs_water else "SKIP WATERING",
        "confidence": "HIGH" if needs_water or (last_rainfall_inches > 0.5 and days_since_rain < 2) else "MEDIUM",
        "reason": reason,
        "lawn_size_sqft": lawn_size_sqft,
        "soil_type": soil_type,
        "days_since_last_watering": round(days_since_watered, 1),
        "days_since_last_rainfall": round(days_since_rain, 1),
        "rainfall_amount_inches": last_rainfall_inches,
        "water_requirement_weekly_inches": round(weekly_requirement, 2),
        "water_requirement_daily_inches": round(daily_watering, 3),
        "estimated_gallons_needed": round(
            (weekly_requirement * lawn_size_sqft / 1000) * 62.3, 0
        ),
        "recommended_frequency": f"Every {retention:.1f} days",
        "best_time_to_water": "Early morning (5-9 AM) to minimize evaporation",
        "irrigation_method": "Sprinkler or drip system for even coverage",
        "watering_duration_minutes": calculate_duration(weekly_requirement, lawn_size_sqft),
        "drought_stress_risk": assess_drought_risk(days_since_watered, retention),
        "notes": get_watering_notes(needs_water, soil_type)
    }
    
    return recommendation


def calculate_duration(inches_needed: float, lawn_sqft: int) -> int:
    """Calculate sprinkler run time based on typical output."""
    # Typical sprinkler: 0.5-1 inch per hour depending on spacing
    # Assume 0.75 inches per hour average
    rate_per_hour = 0.75
    return max(30, int((inches_needed / rate_per_hour) * 60 / 7))  # Minutes


def assess_drought_risk(days_since: float, retention: float) -> str:
    """Assess drought stress risk."""
    if days_since > retention * 1.5:
        return "HIGH - Water immediately"
    elif days_since > retention:
        return "MODERATE - Water today"
    elif days_since > retention * 0.5:
        return "LOW - Plan to water within 24-48 hours"
    else:
        return "MINIMAL - Not needed soon"


def get_watering_notes(needs_water: bool, soil_type: str) -> str:
    """Get specific watering advice."""
    notes = f"Soil type: {soil_type}. "
    
    if soil_type == "clay":
        notes += "Clay holds water well but can become compacted. Use moderate pressure to avoid damage."
    elif soil_type == "sand":
        notes += "Sandy soil drains quickly. Water more frequently but for shorter periods."
    else:  # loam
        notes += "Loam has good water retention. Follow standard watering schedule."
    
    if needs_water:
        notes += " IMPORTANT: Grass showing stress signs - prioritize watering."
    
    return notes


if __name__ == "__main__":
    # CLI interface
    if len(sys.argv) > 1:
        lawn_size = int(sys.argv[1])
        soil = sys.argv[2] if len(sys.argv) > 2 else "loam"
        watered = int(sys.argv[3]) if len(sys.argv) > 3 else 72
        result = watering_decision(lawn_size, soil, None, watered)
    else:
        # Default example: 5000 sq ft, loam soil, last watered 4 days ago
        result = watering_decision(5000, "loam", None, 96)
    
    print(json.dumps(result, indent=2))
