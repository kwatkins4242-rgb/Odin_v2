"""
Sensor Manager - Coordinate multiple sensor inputs
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class SensorManager:
    """Manage and coordinate all sensor inputs"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sensors = {}
        self.sensor_data = {}
        self.alert_thresholds = {}
        
    async def register_sensor(self, sensor_id: str, sensor_type: str, 
                            config: Dict[str, Any]) -> bool:
        """Register a new sensor"""
        try:
            self.sensors[sensor_id] = {
                "type": sensor_type,
                "config": config,
                "status": "active",
                "last_read": None
            }
            
            # Set default thresholds if provided
            if "thresholds" in config:
                self.alert_thresholds[sensor_id] = config["thresholds"]
                
            self.logger.info(f"Sensor {sensor_id} registered as {sensor_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register sensor {sensor_id}: {e}")
            return False
            
    async def read_sensor(self, sensor_id: str) -> Dict[str, Any]:
        """Read data from a specific sensor"""
        if sensor_id not in self.sensors:
            return {"error": f"Sensor {sensor_id} not found"}
            
        try:
            sensor = self.sensors[sensor_id]
            sensor_type = sensor["type"]
            config = sensor["config"]
            
            # Simulate sensor reading (in real implementation, this would
            # interface with actual hardware)
            reading = await self.simulate_sensor_reading(sensor_type, config)
            
            # Store reading
            self.sensor_data[sensor_id] = {
                "timestamp": datetime.now().isoformat(),
                "value": reading["value"],
                "unit": reading.get("unit", ""),
                "status": reading.get("status", "ok")
            }
            
            # Update sensor status
            sensor["last_read"] = datetime.now()
            
            # Check for alerts
            alerts = self.check_alerts(sensor_id, reading["value"])
            
            return {
                "sensor_id": sensor_id,
                "reading": self.sensor_data[sensor_id],
                "alerts": alerts
            }
            
        except Exception as e:
            self.logger.error(f"Failed to read sensor {sensor_id}: {e}")
            return {"error": str(e)}
            
    async def read_all_sensors(self, system_id: str) -> Dict[str, Any]:
        """Read all sensors for a system"""
        system_sensors = [
            sid for sid, sensor in self.sensors.items() 
            if sensor["config"].get("system_id") == system_id
        ]
        
        if not system_sensors:
            # For demonstration, if no sensors found, register some defaults
            await self.register_sensor("temp_01", "temperature", {"system_id": system_id, "base_value": 25.0, "thresholds": {"high": 35.0}})
            await self.register_sensor("press_01", "pressure", {"system_id": system_id, "base_value": 101.3})
            system_sensors = ["temp_01", "press_01"]
            
        results = {}
        for sensor_id in system_sensors:
            results[sensor_id] = await self.read_sensor(sensor_id)
            
        return {
            "system_id": system_id,
            "sensor_count": len(system_sensors),
            "readings": results,
            "timestamp": datetime.now().isoformat()
        }
            
    async def simulate_sensor_reading(self, sensor_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate sensor reading (for demonstration)"""
        import random
        
        # Simulate different sensor types
        if sensor_type == "temperature":
            base_temp = config.get("base_value", 20.0)
            variation = config.get("variation", 5.0)
            value = base_temp + random.uniform(-variation, variation)
            return {"value": round(value, 2), "unit": "°C"}
            
        elif sensor_type == "pressure":
            base_pressure = config.get("base_value", 100.0)
            variation = config.get("variation", 10.0)
            value = base_pressure + random.uniform(-variation, variation)
            return {"value": round(value, 2), "unit": "kPa"}
            
        elif sensor_type == "flow_rate":
            base_flow = config.get("base_value", 10.0)
            variation = config.get("variation", 2.0)
            value = base_flow + random.uniform(-variation, variation)
            return {"value": round(value, 2), "unit": "L/min"}
            
        elif sensor_type == "voltage":
            base_voltage = config.get("base_value", 12.0)
            variation = config.get("variation", 1.0)
            value = base_voltage + random.uniform(-variation, variation)
            return {"value": round(value, 2), "unit": "V"}
            
        elif sensor_type == "current":
            base_current = config.get("base_value", 5.0)
            variation = config.get("variation", 0.5)
            value = base_current + random.uniform(-variation, variation)
            return {"value": round(value, 2), "unit": "A"}
            
        else:
            # Generic sensor simulation
            base_value = config.get("base_value", 0.0)
            variation = config.get("variation", 1.0)
            value = base_value + random.uniform(-variation, variation)
            unit = config.get("unit", "units")
            return {"value": round(value, 2), "unit": unit}
            
    def check_alerts(self, sensor_id: str, value: float) -> List[Dict[str, Any]]:
        """Check if sensor reading triggers alerts"""
        alerts = []
        
        if sensor_id not in self.alert_thresholds:
            return alerts
            
        thresholds = self.alert_thresholds[sensor_id]
        
        # Check high threshold
        if "high" in thresholds and value > thresholds["high"]:
            alerts.append({
                "type": "high_threshold",
                "sensor_id": sensor_id,
                "value": value,
                "threshold": thresholds["high"],
                "severity": "warning" if value < thresholds["high"] * 1.1 else "critical"
            })
            
        # Check low threshold
        if "low" in thresholds and value < thresholds["low"]:
            alerts.append({
                "type": "low_threshold",
                "sensor_id": sensor_id,
                "value": value,
                "threshold": thresholds["low"],
                "severity": "warning" if value > thresholds["low"] * 0.9 else "critical"
            })
            
        return alerts
        
    async def get_sensor_status(self, sensor_id: str) -> Dict[str, Any]:
        """Get current status of a sensor"""
        if sensor_id not in self.sensors:
            return {"error": f"Sensor {sensor_id} not found"}
            
        sensor = self.sensors[sensor_id]
        last_reading = self.sensor_data.get(sensor_id)
        
        return {
            "sensor_id": sensor_id,
            "type": sensor["type"],
            "status": sensor["status"],
            "last_read": sensor["last_read"],
            "current_reading": last_reading
        }
