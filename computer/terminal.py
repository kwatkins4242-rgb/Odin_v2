"""
Terminal Controller - Execute system commands safely
"""

import subprocess
import asyncio
import logging
import shlex
from typing import Dict, Any, List
import platform

class TerminalController:
    """Execute terminal commands with safety checks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.allowed_commands = {
            'ls', 'dir', 'pwd', 'cd', 'cat', 'type', 'echo', 'grep', 'find', 'which',
            'python', 'python3', 'pip', 'npm', 'node', 'git', 'docker', 'kubectl',
            'ps', 'top', 'htop', 'df', 'du', 'free', 'vmstat', 'iostat',
            'netstat', 'ss', 'ping', 'curl', 'wget', 'ssh', 'scp'
        }
        
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a terminal command"""
        self.logger.info(f"Executing command: {command}")
        
        try:
            # Parse command
            if command.startswith("terminal.execute"):
                cmd_args = kwargs.get("command", "")
            else:
                cmd_args = kwargs.get("args", "")
                
            # Safety check
            if not self.is_command_safe(cmd_args):
                return {"error": "Command not allowed for security reasons"}
                
            # Execute command
            result = await self.run_command(cmd_args)
            
            return {
                "command": cmd_args,
                "output": result["output"],
                "error": result.get("error"),
                "return_code": result["return_code"]
            }
            
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {"error": str(e)}
            
    def is_command_safe(self, command: str) -> bool:
        """Check if command is safe to execute"""
        # Parse command to get the base command
        try:
            parts = shlex.split(command)
            if not parts:
                return False
                
            base_cmd = parts[0].lower()
            
            # Check against allowed commands
            return base_cmd in self.allowed_commands
            
        except Exception:
            return False
            
    async def run_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Run command with timeout"""
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return {
                "output": stdout.decode() if stdout else "",
                "error": stderr.decode() if stderr else None,
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            process.kill()
            return {
                "output": "",
                "error": "Command timed out",
                "return_code": -1
            }
            
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }
