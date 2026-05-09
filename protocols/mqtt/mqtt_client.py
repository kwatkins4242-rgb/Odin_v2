"""
COMMS — MQTT Client
The backbone of ODIN's smart home control.
MQTT is how most smart devices talk — lights, thermostats, sensors, plugs.

ODIN publishes commands and subscribes to device state updates.
Every device that supports MQTT can be controlled and monitored.

Broker: Install Mosquitto locally for fully offline control:
  apt install mosquitto mosquitto-clients
  systemctl start mosquitto
"""

import os
import json
import time
import threading
from typing import Optional, Callable
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER   = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT     = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "odin-comms")


class MQTTClient:

    def __init__(self):
        self._client     = None
        self._connected  = False
        self._callbacks  = {}  # topic → callback function
        self._subscriptions = []

    def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(client_id=MQTT_CLIENT_ID, clean_session=True)

            if MQTT_USERNAME:
                self._client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

            self._client.on_connect    = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message    = self._on_message

            self._client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self._client.loop_start()  # Background thread

            # Wait for connection
            for _ in range(20):
                if self._connected:
                    return True
                time.sleep(0.1)

            return self._connected

        except ImportError:
            print("[MQTT] paho-mqtt not installed")
            return False
        except Exception as e:
            print(f"[MQTT] Connect error: {e}")
            return False

    def publish(self, topic: str, payload, retain: bool = False) -> bool:
        """Publish a message to an MQTT topic."""
        if not self._client or not self._connected:
            self.connect()
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            elif not isinstance(payload, str):
                payload = str(payload)

            result = self._client.publish(topic, payload, qos=1, retain=retain)
            return result.rc == 0
        except Exception as e:
            print(f"[MQTT] Publish error: {e}")
            return False

    def publish_command(self, topic: str, command: str, value: Optional[str] = None) -> dict:
        """Publish a device command in ODIN's standard format."""
        payload = {"command": command}
        if value is not None:
            payload["value"] = value
        payload["timestamp"] = time.time()
        success = self.publish(topic, payload)
        return {"published": success, "topic": topic, "payload": payload}

    def subscribe(self, topic: str, callback: Callable = None):
        """
        Subscribe to an MQTT topic.
        callback(topic, payload) will be called when a message arrives.
        """
        if not self._connected:
            self.connect()
        try:
            self._client.subscribe(topic, qos=1)
            if callback:
                self._callbacks[topic] = callback
            self._subscriptions.append(topic)
            print(f"[MQTT] Subscribed: {topic}")
        except Exception as e:
            print(f"[MQTT] Subscribe error: {e}")

    def subscribe_device_states(self):
        """
        Subscribe to all known device state topics.
        ODIN gets notified when any device changes state.
        """
        from discovery.device_registry import DeviceRegistry
        registry = DeviceRegistry()
        for device in registry.get_all():
            state_topic = device.get("state_topic")
            if state_topic:
                self.subscribe(state_topic, self._handle_state_update)

    def _handle_state_update(self, topic: str, payload: dict):
        """Called when a device reports a state change."""
        from discovery.device_registry import DeviceRegistry
        registry = DeviceRegistry()
        # Find device by state topic and update its last known state
        for device in registry.get_all():
            if device.get("state_topic") == topic:
                device["last_state"] = payload
                device["last_seen"]  = time.time()
                registry.update(device)
                break

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"[MQTT] Connected to {MQTT_BROKER}:{MQTT_PORT}")
            # Resubscribe after reconnect
            for topic in self._subscriptions:
                client.subscribe(topic, qos=1)
        else:
            print(f"[MQTT] Connection failed (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            print(f"[MQTT] Unexpected disconnect (rc={rc}) — will auto-reconnect")

    def _on_message(self, client, userdata, msg):
        topic   = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except:
            payload = msg.payload.decode()

        # Call registered callback
        if topic in self._callbacks:
            self._callbacks[topic](topic, payload)

        # Wildcard matching
        for pattern, callback in self._callbacks.items():
            if "+" in pattern or "#" in pattern:
                if self._topic_matches(pattern, topic):
                    callback(topic, payload)

    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """MQTT wildcard matching (+ and #)."""
        p_parts = pattern.split("/")
        t_parts = topic.split("/")
        for i, p in enumerate(p_parts):
            if p == "#":
                return True
            if i >= len(t_parts):
                return False
            if p != "+" and p != t_parts[i]:
                return False
        return len(p_parts) == len(t_parts)

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected
