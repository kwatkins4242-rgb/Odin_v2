"""
File Manager - Create, read, modify, and delete files safely
"""

import os
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

class FileManager:
    """Manage file operations with safety checks"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.allowed_extensions = {
            '.txt', '.md', '.json', '.yaml', '.yml', '.csv', '.log',
            '.py', '.js', '.html', '.css', '.xml', '.sql',
            '.doc', '.docx', '.pdf', '.xls', '.xlsx'
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute file management command"""
        self.logger.info(f"Executing file command: {command}")
        
        try:
            if command == "file.create":
                return await self.create_file(**kwargs)
            elif command == "file.read":
                return await self.read_file(**kwargs)
            elif command == "file.modify":
                return await self.modify_file(**kwargs)
            elif command == "file.delete":
                return await self.delete_file(**kwargs)
            elif command == "file.list":
                return await self.list_files(**kwargs)
            elif command == "file.copy":
                return await self.copy_file(**kwargs)
            elif command == "file.move":
                return await self.move_file(**kwargs)
            else:
                return {"error": f"Unknown file command: {command}"}
                
        except Exception as e:
            self.logger.error(f"File operation failed: {e}")
            return {"error": str(e)}
            
    async def create_file(self, path: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
        """Create a new file"""
        try:
            file_path = Path(path)
            
            # Safety checks
            if not self.is_path_safe(file_path):
                return {"error": "Path not allowed for security reasons"}
                
            if file_path.exists() and not overwrite:
                return {"error": "File already exists and overwrite is False"}
                
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return {
                "status": "created",
                "path": str(file_path),
                "size": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    async def read_file(self, path: str, max_size: int = None) -> Dict[str, Any]:
        """Read file contents"""
        try:
            file_path = Path(path)
            
            # Safety checks
            if not self.is_path_safe(file_path):
                return {"error": "Path not allowed for security reasons"}
                
            if not file_path.exists():
                return {"error": "File does not exist"}
                
            # Check file size
            file_size = file_path.stat().st_size
            max_read_size = max_size or self.max_file_size
            
            if file_size > max_read_size:
                return {"error": f"File too large (>{max_read_size} bytes)"}
                
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return {
                "status": "read",
                "path": str(file_path),
                "content": content,
                "size": file_size
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    async def modify_file(self, path: str, content: str, mode: str = "overwrite") -> Dict[str, Any]:
        """Modify file contents"""
        try:
            file_path = Path(path)
            
            # Safety checks
            if not self.is_path_safe(file_path):
                return {"error": "Path not allowed for security reasons"}
                
            if not file_path.exists():
                return {"error": "File does not exist"}
                
            if mode == "overwrite":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif mode == "append":
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
            else:
                return {"error": f"Unknown modify mode: {mode}"}
                
            return {
                "status": "modified",
                "path": str(file_path),
                "mode": mode
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            file_path = Path(path)
            
            # Safety checks
            if not self.is_path_safe(file_path):
                return {"error": "Path not allowed for security reasons"}
                
            if not file_path.exists():
                return {"error": "File does not exist"}
                
            file_path.unlink()
            
            return {
                "status": "deleted",
                "path": str(file_path)
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    async def list_files(self, directory: str, pattern: str = "*") -> Dict[str, Any]:
        """List files in directory"""
        try:
            dir_path = Path(directory)
            
            # Safety checks
            if not self.is_path_safe(dir_path):
                return {"error": "Path not allowed for security reasons"}
                
            if not dir_path.exists():
                return {"error": "Directory does not exist"}
                
            if not dir_path.is_dir():
                return {"error": "Path is not a directory"}
                
            # List files
            files = list(dir_path.glob(pattern))
            
            file_list = []
            for file_path in files:
                if file_path.is_file():
                    stat = file_path.stat()
                    file_list.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
                    
            return {
                "status": "listed",
                "directory": str(dir_path),
                "files": file_list,
                "count": len(file_list)
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    def is_path_safe(self, path: Path) -> bool:
        """Check if file path is safe"""
        try:
            # Resolve to absolute path
            abs_path = path.resolve()
            
            # Check file extension
            if path.suffix and path.suffix.lower() not in self.allowed_extensions:
                return False
                
            # Prevent access to system directories (basic check)
            # On Windows, we check for common sensitive folders
            sensitive_patterns = ['Windows', 'Program Files', 'System32']
            path_str = str(abs_path)
            for pattern in sensitive_patterns:
                if pattern in path_str:
                    # Allow if it's within ODIN path
                    if 'Odin' in path_str:
                        continue
                    return False
                    
            return True
            
        except Exception:
            return False
