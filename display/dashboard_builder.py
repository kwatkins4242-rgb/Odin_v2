"""
Dashboard Builder - Create real-time data dashboards
"""

import asyncio
import logging
from typing import Dict, Any, List
import json
from datetime import datetime

class DashboardBuilder:
    """Build and manage real-time data dashboards"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dashboards = {}
        self.widget_templates = self.load_widget_templates()
        
    def load_widget_templates(self) -> Dict[str, Any]:
        """Load available widget templates"""
        return {
            "gauge": {
                "type": "gauge",
                "title": "Gauge Widget",
                "min_value": 0,
                "max_value": 100,
                "units": "",
                "color_ranges": {
                    "normal": {"min": 0, "max": 70, "color": "green"},
                    "warning": {"min": 70, "max": 90, "color": "yellow"},
                    "critical": {"min": 90, "max": 100, "color": "red"}
                }
            },
            "line_chart": {
                "type": "line_chart",
                "title": "Line Chart",
                "x_axis": "Time",
                "y_axis": "Value",
                "time_range": "1h",
                "update_interval": "1s"
            },
            "bar_chart": {
                "type": "bar_chart",
                "title": "Bar Chart",
                "orientation": "vertical"
            },
            "status_indicator": {
                "type": "status_indicator",
                "title": "Status",
                "states": {
                    "ok": {"color": "green", "icon": "check"},
                    "warning": {"color": "yellow", "icon": "warning"},
                    "error": {"color": "red", "icon": "error"}
                }
            },
            "data_table": {
                "type": "data_table",
                "title": "Data Table",
                "columns": ["Parameter", "Value", "Unit", "Status"]
            }
        }
        
    async def create_dashboard(self, dashboard_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard"""
        try:
            dashboard = {
                "id": dashboard_id,
                "title": config.get("title", "Dashboard"),
                "description": config.get("description", ""),
                "created": datetime.now().isoformat(),
                "widgets": {},
                "layout": config.get("layout", "grid"),
                "update_interval": config.get("update_interval", "5s"),
                "auto_refresh": config.get("auto_refresh", True)
            }
            
            self.dashboards[dashboard_id] = dashboard
            
            self.logger.info(f"Dashboard {dashboard_id} created")
            return {"status": "created", "dashboard": dashboard}
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard {dashboard_id}: {e}")
            return {"error": str(e)}
            
    async def add_widget(self, dashboard_id: str, widget_id: str, 
                        widget_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a widget to a dashboard"""
        if dashboard_id not in self.dashboards:
            return {"error": f"Dashboard {dashboard_id} not found"}
            
        try:
            # Get widget template
            if widget_type not in self.widget_templates:
                return {"error": f"Widget type {widget_type} not supported"}
                
            template = self.widget_templates[widget_type].copy()
            template.update(config)
            template["id"] = widget_id
            template["created"] = datetime.now().isoformat()
            
            # Add to dashboard
            self.dashboards[dashboard_id]["widgets"][widget_id] = template
            
            self.logger.info(f"Widget {widget_id} added to dashboard {dashboard_id}")
            return {"status": "added", "widget": template}
            
        except Exception as e:
            self.logger.error(f"Failed to add widget {widget_id}: {e}")
            return {"error": str(e)}
            
    async def update_dashboard(self, dashboard_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update dashboard with new data"""
        if dashboard_id not in self.dashboards:
            await self.create_dashboard(dashboard_id, {"title": f"System {dashboard_id} Dashboard"})
            
        try:
            dashboard = self.dashboards[dashboard_id]
            
            # If dashboard has no widgets, add a default status indicator
            if not dashboard["widgets"]:
                await self.add_widget(dashboard_id, "status_01", "status_indicator", {"title": "Overall Status"})
                await self.add_widget(dashboard_id, "temp_gauge", "gauge", {"title": "Core Temperature", "max_value": 100})
            
            # Update each widget with relevant data
            for widget_id, widget in dashboard["widgets"].items():
                widget_data = self.extract_widget_data(widget, data)
                widget["data"] = widget_data
                widget["last_updated"] = datetime.now().isoformat()
                
            dashboard["last_updated"] = datetime.now().isoformat()
            
            return {
                "status": "updated",
                "dashboard_id": dashboard_id,
                "widget_count": len(dashboard["widgets"]),
                "timestamp": dashboard["last_updated"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update dashboard {dashboard_id}: {e}")
            return {"error": str(e)}
            
    def extract_widget_data(self, widget: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant data for a widget"""
        widget_type = widget["type"]
        
        if widget_type == "gauge":
            # Extract single value for gauge
            value_key = widget.get("data_key", "value")
            if value_key in data:
                return {"value": data[value_key]}
            elif "sensors" in data:
                # Use first sensor value
                sensor_data = list(data["sensors"].values())[0]
                # Handle nested reading
                if isinstance(sensor_data, dict) and "reading" in sensor_data:
                    return {"value": sensor_data["reading"].get("value", 0)}
                return {"value": sensor_data.get("value", 0)}
                
        elif widget_type == "line_chart":
            # Extract time series data
            if "history" in data:
                return {"series": data["history"]}
            elif "sensors" in data:
                # Create series from multiple sensors
                series = []
                for sensor_id, reading in data["sensors"].items():
                    val = reading.get("value", 0)
                    if isinstance(reading, dict) and "reading" in reading:
                        val = reading["reading"].get("value", 0)
                    series.append({
                        "name": sensor_id,
                        "value": val,
                        "timestamp": datetime.now().isoformat()
                    })
                return {"series": series}
                
        elif widget_type == "status_indicator":
            # Extract status information
            if "diagnostics" in data:
                diagnostics = data["diagnostics"]
                if diagnostics.get("alerts"):
                    return {"status": "error", "message": f"{len(diagnostics['alerts'])} alerts"}
                elif diagnostics.get("warnings"):
                    return {"status": "warning", "message": f"{len(diagnostics['warnings'])} warnings"}
                else:
                    return {"status": "ok", "message": "System OK"}
            elif "sensors" in data:
                # Check if any sensors have alerts
                has_alerts = any("alerts" in reading and reading["alerts"] for reading in data["sensors"].values())
                if has_alerts:
                    return {"status": "warning", "message": "Sensor alerts detected"}
                else:
                    return {"status": "ok", "message": "All sensors OK"}
                    
        elif widget_type == "data_table":
            # Extract tabular data
            table_data = []
            if "sensors" in data:
                for sensor_id, reading in data["sensors"].items():
                    val = reading.get("value", 0)
                    unit = reading.get("unit", "")
                    status = reading.get("status", "unknown")
                    if isinstance(reading, dict) and "reading" in reading:
                        val = reading["reading"].get("value", 0)
                        unit = reading["reading"].get("unit", "")
                        status = reading["reading"].get("status", "unknown")
                    table_data.append({
                        "Parameter": sensor_id,
                        "Value": val,
                        "Unit": unit,
                        "Status": status
                    })
            return {"data": table_data}
            
        return {}
        
    async def get_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard configuration and data"""
        if dashboard_id not in self.dashboards:
            return {"error": f"Dashboard {dashboard_id} not found"}
            
        return self.dashboards[dashboard_id]
        
    async def list_dashboards(self) -> List[Dict[str, Any]]:
        """List all dashboards"""
        return [
            {
                "id": dash_id,
                "title": dash["title"],
                "description": dash["description"],
                "widget_count": len(dash["widgets"]),
                "created": dash["created"],
                "last_updated": dash.get("last_updated")
            }
            for dash_id, dash in self.dashboards.items()
        ]
