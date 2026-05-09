import re
import json
import httpx
import logging
from pathlib import Path

logger = logging.getLogger("odin.dispatcher")

class ToolDispatcher:
    def __init__(self, bridge_url: str, bridge_key: str):
        self.bridge_url = bridge_url
        self.bridge_key = bridge_key
        # Regex to find [TOOL: name {json_payload}]
        self.tool_pattern = re.compile(r"\[TOOL:\s*(\w+)\s*(\{.*?\})\]", re.DOTALL)

    async def execute_all(self, text: str) -> list:
        """Find all tools in text and execute them. Returns list of (tool, result)."""
        matches = self.tool_pattern.findall(text)
        results = []
        
        for tool_name, payload_str in matches:
            try:
                payload = json.loads(payload_str)
                logger.info(f"[Dispatcher] Executing {tool_name} with {payload}")
                
                result = await self.call_bridge(tool_name, payload)
                results.append((tool_name, result))
                
            except Exception as e:
                logger.error(f"[Dispatcher] Failed to parse/execute {tool_name}: {e}")
                results.append((tool_name, f"Error: {str(e)}"))
                
        return results

    async def call_bridge(self, tool_name: str, payload: dict) -> str:
        """Call the Agent Bridge for a specific task."""
        try:
            # Map tool names to Bridge tasks
            task_map = {
                "list_dir": "list_dir",
                "read_file": "read_file",
                "write_file": "write_file",
                "delete_file": "delete_file",
                "make_dir": "make_dir",
                "mkdir": "make_dir",
                "move_file": "move_file",
                "run_command": "run_command",
                "memory_search": "memory_search",
                "see": "take_screenshot",
            }
            
            task = task_map.get(tool_name)
            if not task:
                return f"Unknown tool: {tool_name}"

            headers = {}
            if self.bridge_key:
                headers["X-ODIN-KEY"] = self.bridge_key
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    f"{self.bridge_url.rstrip('/')}/n8n/trigger",
                    json={
                        "task": task,
                        "payload": payload,
                        "api_key": self.bridge_key,
                    },
                    headers=headers,
                )
                
                if r.status_code == 200:
                    data = r.json()
                    if data.get("success"):
                        return json.dumps(data.get("data", {}), indent=2)
                    return f"Error: {data.get('error', 'Unknown bridge error')}"
                return f"Bridge HTTP Error: {r.status_code}"
                
        except httpx.TimeoutException:
            return "Error: Bridge request timed out. The system may be busy."
        except Exception as e:
            return f"Bridge connection failed: {str(e)}"

def format_observation(tool_name: str, result: str) -> str:
    """Format the tool output for the AI's context."""
    return f"\n\n[OBSERVATION: {tool_name}]\n{result}\n[END OBSERVATION]\n"
