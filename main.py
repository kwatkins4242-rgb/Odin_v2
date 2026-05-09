#!/usr/bin/env python3
"""
M3: SENSE & ACT
Main entry point for ODIN's autonomous loop.
Integrates Vision, Tool Calling, and Mouse/Keyboard control.
"""

import asyncio
import logging
import os
import json
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import SDK modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sdk'))

try:
    from vision_tool import capture_screen, analyze_screen
    from tool_call import client, MODEL, get_weather
    import mouse_control
except ImportError as e:
    print(f"Error importing SDK modules: {e}")

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

class OdinAgent:
    """Main ODIN autonomous agent orchestrator"""
    
    def __init__(self):
        self.setup_logging()
        self.running = False
        self.vision_interval = 300  # 5 minutes
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('odin_agent.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("ODIN-AGENT")
        
    async def sense(self):
        """Capture environmental data (Vision)"""
        self.logger.info("Sensing environment...")
        try:
            filepath = capture_screen()
            analysis = analyze_screen(filepath, prompt="What is happening on the screen? Identify any tasks or notifications.")
            self.logger.info(f"Sense analysis: {analysis}")
            return {"type": "vision", "content": analysis, "file": filepath}
        except Exception as e:
            self.logger.error(f"Sensing failed: {e}")
            return {"error": str(e)}

    async def think_and_act(self, sense_data: Dict[str, Any]):
        """Decide what to do based on sense data and current state"""
        self.logger.info("Thinking...")
        
        prompt = f"System Status: {sense_data.get('content')}\nUser Instructions: Maintain system stability and respond to notifications."
        
        messages = [
            {"role": "system", "content": "You are ODIN, an autonomous AI agent. Use your tools to help the user. Always respond in JSON format if calling a tool."},
            {"role": "user", "content": prompt}
        ]
        
        # Tools available to the agent
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {"type": "object", "properties": {"location": {"type": "string"}}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mouse_move",
                    "description": "Move the mouse to a specific location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"}
                        },
                        "required": ["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mouse_click",
                    "description": "Click the mouse at a specific location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                            "button": {"type": "string", "enum": ["left", "right", "middle"]}
                        },
                        "required": ["x", "y"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description": "Type a string of text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "interval": {"type": "number"}
                        },
                        "required": ["text"]
                    }
                }
            }
        ]

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                for tool_call in tool_calls:
                    fname = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    self.logger.info(f"Executing tool: {fname} with {args}")
                    
                    if fname == "get_weather":
                        res = get_weather(**args)
                        self.logger.info(f"Tool result: {res}")
                    elif fname == "mouse_move":
                        mouse_control.mouse_move(**args)
                        self.logger.info("Mouse moved.")
                    elif fname == "mouse_click":
                        mouse_control.mouse_click(**args)
                        self.logger.info(f"Clicked {args.get('button', 'left')} at {args['x']}, {args['y']}")
                    elif fname == "type_text":
                        mouse_control.type_text(**args)
                        self.logger.info(f"Typed text: {args['text']}")
            else:
                self.logger.info(f"Agent feedback: {response_message.content}")

        except Exception as e:
            self.logger.error(f"Thinking failed: {e}")

    async def loop(self):
        """Main autonomous loop"""
        self.logger.info("ODIN Autonomous Loop starting...")
        self.running = True
        
        while self.running:
            sense_data = await self.sense()
            await self.think_and_act(sense_data)
            
            self.logger.info(f"Sleeping for {self.vision_interval} seconds...")
            await asyncio.sleep(self.vision_interval)

    def stop(self):
        self.running = False
        self.logger.info("ODIN Autonomous Loop stopping...")

if __name__ == "__main__":
    agent = OdinAgent()
    try:
        asyncio.run(agent.loop())
    except KeyboardInterrupt:
        agent.stop()
