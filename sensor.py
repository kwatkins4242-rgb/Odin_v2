
sensor.py

async def register_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        config: Dict[str, Any]
    ) -> bool:
        try:
            self.sensors[sensor_id] = {
                "type": sensor_type,
                "config": config,
                "status": "active",
                "last_read": None
            }
            if "thresholds" in config:
                self.alert_thresholds[sensor_id] = config["thresholds"]
            logger.info("Sensor %s registered as %s", sensor_id, sensor_type)
            return True
        except Exception as e:
            logger.exception("Failed to register sensor %s", sensor_id)
            return False