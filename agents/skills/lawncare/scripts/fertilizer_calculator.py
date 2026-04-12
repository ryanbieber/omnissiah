#!/usr/bin/env python3
"""
Fertilizer calculator tool for lawn care.
Calculates optimal nitrogen rates based on grass type, season, and soil conditions.
"""
import json
import sys
from typing import Dict, Optional


def fertilizer_calculator(
    lawn_size_sqft: int,
    grass_type: str = "cool-season",
    season: str = "fall",
    soil_test: Optional[Dict] = None
) -> Dict:
    """
    Calculate optimal fertilizer application rates.
    
    Args:
        lawn_size_sqft: Size of lawn in square feet
        grass_type: Type of grass (cool-season, warm-season)
        season: Current season (spring, summer, fall)
        soil_test: Optional soil test results (N, P, K levels)
    
    Returns:
        Fertilizer recommendation with rates and product suggestions
    """
    
    # Annual N budget for cool-season grass: 2-4 lbs N per 1000 sq ft
    annual_n_budget = 3.5  # lbs per 1000 sq ft (mid-range)
    
    # Seasonal allocation (percent of annual)
    seasonal_allocation = {
        "spring": 0.25,      # 25% - spring green-up
        "summer": 0.10,      # 10% - minimal, heat stress risk
        "early_fall": 0.45,  # 45% - most critical for winter
        "fall": 0.20         # 20% - final push
    }
    
    # Get seasonal percentage
    allocation = seasonal_allocation.get(season, 0.25)
    
    # Calculate N needed for this application
    lawn_size_k_sqft = lawn_size_sqft / 1000
    n_needed = annual_n_budget * allocation * lawn_size_k_sqft
    
    # Recommended ratios by season
    ratios = {
        "spring": {"n": 10, "p": 20, "k": 20},      # Higher P and K for root growth
        "summer": {"n": 12, "p": 8, "k": 8},        # Lower rates, higher N
        "early_fall": {"n": 10, "p": 10, "k": 20},  # High K for winter hardiness
        "fall": {"n": 10, "p": 10, "k": 20}         # Similar to early_fall
    }
    
    ratio = ratios.get(season, ratios["spring"])
    
    # Calculate actual product rates
    # If using 10-20-20 with 10 lbs N per 1000 sq ft
    product_amount_per_k = n_needed / ratio["n"] * 10 if ratio["n"] > 0 else 0
    
    recommendation = {
        "lawn_size_sqft": lawn_size_sqft,
        "grass_type": grass_type,
        "season": season,
        "nitrogen_needed_lbs": round(n_needed, 2),
        "phosphorus_needed_lbs": round(n_needed * ratio["p"] / ratio["n"], 2),
        "potassium_needed_lbs": round(n_needed * ratio["k"] / ratio["n"], 2),
        "recommended_ratio": f"{ratio['n']}-{ratio['p']}-{ratio['k']}",
        "estimated_product_needed_lbs": round(product_amount_per_k, 2),
        "suggested_products": get_product_suggestions(season),
        "application_rate_lbs_per_k_sqft": round(product_amount_per_k / lawn_size_k_sqft, 2),
        "watering_after_application": "Optional - water in if no rain expected within 48h",
        "notes": get_seasonal_notes(season)
    }
    
    return recommendation


def get_product_suggestions(season: str) -> list:
    """Get recommended fertilizer products for the season."""
    suggestions = {
        "spring": [
            {"name": "Scotts Turf Builder", "ratio": "24-0-4", "type": "granular"},
            {"name": "Milorganite", "ratio": "6-2-0", "type": "organic"},
            {"name": "Espoma Organic Lawn Food", "ratio": "10-0-1", "type": "organic"}
        ],
        "summer": [
            {"name": "Slow Release Lawn Fertilizer", "ratio": "26-0-3", "type": "granular"},
            {"name": "Liquid Lawn Food", "ratio": "24-0-8", "type": "liquid"}
        ],
        "early_fall": [
            {"name": "Scotts Turf Builder Fall", "ratio": "32-0-10", "type": "granular"},
            {"name": "Winter Fertilizer", "ratio": "10-10-20", "type": "granular"},
            {"name": "Fall Prep", "ratio": "12-0-24", "type": "granular"}
        ],
        "fall": [
            {"name": "Scotts Turf Builder Fall", "ratio": "32-0-10", "type": "granular"},
            {"name": "Winter Fertilizer", "ratio": "10-10-20", "type": "granular"}
        ]
    }
    return suggestions.get(season, [])


def get_seasonal_notes(season: str) -> str:
    """Get seasonal-specific advice."""
    notes = {
        "spring": "Apply when soil temp reaches 55-60°F. Promotes spring green-up and growth.",
        "summer": "Minimize nitrogen to prevent heat stress and disease. Water well if applied.",
        "early_fall": "MOST IMPORTANT application. High K builds winter hardiness. Apply Aug 15-Sept 15.",
        "fall": "Final application before dormancy. Lower rates acceptable after early_fall."
    }
    return notes.get(season, "Follow general guidelines for lawn type and region.")


if __name__ == "__main__":
    # CLI interface
    if len(sys.argv) > 1:
        lawn_size = int(sys.argv[1])
        grass_type = sys.argv[2] if len(sys.argv) > 2 else "cool-season"
        season = sys.argv[3] if len(sys.argv) > 3 else "fall"
        result = fertilizer_calculator(lawn_size, grass_type, season)
    else:
        # Default example: 5000 sq ft, cool-season, fall
        result = fertilizer_calculator(5000, "cool-season", "fall")
    
    print(json.dumps(result, indent=2))
