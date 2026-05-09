import os
from pathlib import Path

def scan_project_structure(root_path: str, exclude_dirs: list = None) -> str:
    """Build a text representation of the directory tree."""
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", ".venv", "node_modules", "dist", "build"]
        
    lines = []
    root = Path(root_path)
    
    for current_path, dirs, files in os.walk(root):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        level = Path(current_path).relative_to(root).parts
        indent = "  " * len(level)
        lines.append(f"{indent}📂 {os.path.basename(current_path)}/")
        
        file_indent = "  " * (len(level) + 1)
        for f in sorted(files):
            lines.append(f"{file_indent}📄 {f}")
            
    return "\n".join(lines)

def read_file_snippet(file_path: str, max_lines: int = 100) -> str:
    """Read a snippet of a file for ODIN's context."""
    try:
        p = Path(file_path)
        if not p.exists():
            return f"[ERROR] File {file_path} not found."
            
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        content = "\n".join(lines[:max_lines])
        if len(lines) > max_lines:
            content += f"\n... (truncated {len(lines) - max_lines} more lines)"
        return content
    except Exception as e:
        return f"[ERROR] Could not read {file_path}: {e}"
