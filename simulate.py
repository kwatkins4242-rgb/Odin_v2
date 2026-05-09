




async def read_all_sensors(self, system_id: str) -> Dict[str, Any]:
        system_sensors = [
            sid for sid, sensor in self.sensors.items()
            if sensor["config"].get("system_id") == system_id
        ]

        if not system_sensors:  ### NEW: create demo sensors only once
            await self.register_sensor(
                "temp_01", "temperature",
                {"system_id": system_id, "base_value": 25.0, "thresholds": {"high": 35.0}}
            )
            await self.register_sensor(
                "press_01", "pressure",
                {"system_id": system_id, "base_value": 101.3}
            )
            system_sensors = ["temp_01", "press_01"]

        results = {}
        for sid in system_sensors:
            results[sid] = await self.read_sensor(sid)

        return {
            "system_id": system_id,
            "sensor_count": len(system_sensors),
            "readings": results,
            "timestamp": datetime.now().isoformat()
        }
