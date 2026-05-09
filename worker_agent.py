

def _check_alerts(self, sensor_id: str, value: float) -> List[Dict[str, Any]]:
        alerts = []
        thresholds = self.alert_thresholds.get(sensor_id, {})
        for bound, threshold in thresholds.items():
            if bound == "high" and value > threshold:
                severity = "warning" if value < threshold * 1.1 else "critical"
                alerts.append({
                    "type": "high_threshold", "sensor_id": sensor_id,
                    "value": value, "threshold": threshold, "severity": severity
                })
            elif bound == "low" and value < threshold:
                severity = "warning" if value > threshold * 0.9 else "critical"
                alerts.append({
                    "type": "low_threshold", "sensor_id": sensor_id,
                    "value": value, "threshold": threshold, "severity": severity
                })
        return alerts