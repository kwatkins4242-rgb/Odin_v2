#!/usr/bin/env python3
"""
ODIN-CONTROL: System Control and Automation Hub
Main entry point for computer control, automation, and system management.
"""

import asyncio
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# ── Load .env from ODIN_PRO root ─────────────────────────────────
# load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env", override=True)
load_dotenv(r"Z:\ODIN\ODIN_PRO\.env", override=True)

from computer.terminal import TerminalController
from computer.file_manager import FileManager
from computer.app_controller import AppController
from computer.printer_manager import PrinterManager
from computer.screenshot import ScreenshotManager
from computer.input_controller import InputController
from code_mod.code_executor import CodeExecutor
from code_mod.code_analyzer import CodeAnalyzer
from code_mod.git_manager import GitManager
from code_mod.debugger import Debugger
from smart_home.home_assistant import HomeAssistant
from browser.browser_agent import BrowserAgent
from scheduler.task_scheduler import TaskScheduler

class OdinControl:
    """Main ODIN-CONTROL orchestrator"""
    
    def __init__(self):
        self.setup_logging()
        self.load_modules()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('odin_control.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_modules(self):
        """Initialize all control modules"""
        self.logger.info("Loading ODIN-CONTROL modules...")
        
        # Computer control modules
        self.terminal = TerminalController()
        self.file_manager = FileManager()
        self.app_controller = AppController()
        self.printer_manager = PrinterManager()
        self.screenshot = ScreenshotManager()
        self.input_controller = InputController()
        
        # Code management modules
        self.code_executor = CodeExecutor()
        self.code_analyzer = CodeAnalyzer()
        self.git_manager = GitManager()
        self.debugger = Debugger()
        
        # Smart home modules
        self.home_assistant = HomeAssistant()
        
        # Browser modules
        self.browser = BrowserAgent()
        
        # Scheduler modules
        self.scheduler = TaskScheduler()
        
        self.logger.info("All modules loaded successfully")
        
    async def process_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Process a control command"""
        self.logger.info(f"Processing command: {command}")
        
        try:
            # Route command to appropriate module
            if command.startswith("terminal."):
                return await self.terminal.execute(command, **kwargs)
            elif command.startswith("file."):
                return await self.file_manager.execute(command, **kwargs)
            elif command.startswith("app."):
                return await self.app_controller.execute(command, **kwargs)
            elif command.startswith("code."):
                return await self.code_executor.execute(command, **kwargs)
            elif command.startswith("home."):
                return await self.home_assistant.execute(command, **kwargs)
            elif command.startswith("browser."):
                return await self.browser.execute(command, **kwargs)
            elif command.startswith("schedule."):
                return await self.scheduler.execute(command, **kwargs)
            else:
                return {"error": f"Unknown command: {command}"}
                
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {"error": str(e)}

    async def run(self):
        """Main run loop (standalone usage)"""
        self.logger.info("ODIN-CONTROL started")
        # Logic for standalone run...
        self.logger.info("ODIN-CONTROL shutdown complete")

if __name__ == "__main__":
    control = OdinControl()
    asyncio.run(control.run())
