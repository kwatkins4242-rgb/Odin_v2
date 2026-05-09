sensor_manager.py
sensor_manager.py
```python
"""
Sensor Manager - Coordinate multiple sensor inputs
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import random   ### NEW: moved import to top

logger = logging.getLogger(__name__)


class SensorManager:
    """Manage and coordinate all sensor inputs"""

    def __init__(self):
        self.sensors: Dict[str, Dict[str, Any]] = {}
        self.sensor_data: Dict[str, Dict[str, Any]] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
