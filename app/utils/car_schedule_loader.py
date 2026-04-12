"""Car schedule JSON loader utility"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import Car, MaintenanceItem, MaintenanceType, MaintenanceTask


def load_car_schedule_from_json(json_path: str, db: Session):
    """
    Load car maintenance schedules from JSON file.
    
    Expected JSON format:
    {
        "cars": [
            {
                "name": "Ford Fiesta 2016 ST",
                "make": "Ford",
                "model": "Fiesta",
                "year": 2016,
                "current_miles": 84000,
                "maintenance_schedule": [
                    {
                        "name": "Oil Change",
                        "interval_miles": 5000,
                        "estimated_cost": 50.0,
                        "notes": "Synthetic oil"
                    }
                ]
            }
        ]
    }
    """
    file_path = Path(json_path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    for car_data in data.get("cars", []):
        # Create or update car
        car = db.query(Car).filter(
            Car.make == car_data["make"],
            Car.model == car_data["model"],
            Car.year == car_data["year"]
        ).first()
        
        if not car:
            car = Car(
                name=car_data["name"],
                make=car_data["make"],
                model=car_data["model"],
                year=car_data["year"],
                current_miles=car_data["current_miles"],
            )
            db.add(car)
            db.flush()  # Flush to get the car ID
        
        # Create maintenance items from schedule
        for maintenance_data in car_data.get("maintenance_schedule", []):
            maintenance_item = MaintenanceItem(
                name=maintenance_data["name"],
                description=maintenance_data.get("description"),
                type=MaintenanceType.CAR,
                interval_miles=maintenance_data.get("interval_miles"),
                interval_days=maintenance_data.get("interval_days"),
                car_id=car.id,
                estimated_cost=maintenance_data.get("estimated_cost", 0.0),
                notes=maintenance_data.get("notes"),
            )
            db.add(maintenance_item)
            db.flush()  # Flush to get the item ID
            
            # Create initial maintenance task
            next_due_miles = car.current_miles + maintenance_data.get("interval_miles", 0)
            next_due_date = datetime.utcnow() + timedelta(
                days=maintenance_data.get("interval_days", 365)
            )
            
            task = MaintenanceTask(
                maintenance_item_id=maintenance_item.id,
                status="pending",
                next_due=next_due_date,
            )
            db.add(task)
        
        db.commit()
    
    return True


def export_car_schedule_template():
    """Export a template JSON file for car schedules"""
    template = {
        "cars": [
            {
                "name": "Ford Fiesta 2016 ST",
                "make": "Ford",
                "model": "Fiesta",
                "year": 2016,
                "current_miles": 84000,
                "maintenance_schedule": [
                    {
                        "name": "Oil Change",
                        "description": "Engine oil and filter replacement",
                        "interval_miles": 5000,
                        "interval_days": 365,
                        "estimated_cost": 50.0,
                        "notes": "Synthetic oil recommended"
                    },
                    {
                        "name": "Tire Rotation",
                        "description": "Rotate tires for even wear",
                        "interval_miles": 7500,
                        "estimated_cost": 30.0,
                        "notes": ""
                    },
                    {
                        "name": "Air Filter Replacement",
                        "description": "Replace engine air filter",
                        "interval_miles": 15000,
                        "estimated_cost": 25.0,
                        "notes": ""
                    },
                ]
            },
            {
                "name": "Honda Odyssey 2021",
                "make": "Honda",
                "model": "Odyssey",
                "year": 2021,
                "current_miles": 65000,
                "maintenance_schedule": [
                    {
                        "name": "Oil Change",
                        "description": "Engine oil and filter replacement",
                        "interval_miles": 7500,
                        "estimated_cost": 60.0,
                        "notes": "Synthetic oil"
                    }
                ]
            }
        ]
    }
    
    return template
