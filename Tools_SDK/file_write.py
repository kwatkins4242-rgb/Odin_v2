

from pathlib import Path
from typing import Union


def safe_write(
    path: Union[str, Path],
    content: str,
    mode: str = "w",
    encoding: str = "utf-8",
) -> bool:
    """
    Write content to a file. Verifies the write succeeded.
    No silent failures. Ever.
    Returns True on success. Raises on failure.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, mode, encoding=encoding) as f:
        f.write(content)

    # Verify — the bug that killed the old ODIN dies here
    if mode == "w":
        written = path.read_text(encoding=encoding)
        if written != content:
            raise IOError(f"[ODIN] Write verification failed: {path}")

    return True


def safe_read(path: Union[str, Path], encoding: str = "utf-8") -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"[ODIN] File not found: {path}")
    return path.read_text(encoding=encoding)


def safe_append(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
) -> bool:
    return safe_write(path, content, mode="a", encoding=encoding)


def safe_delete(path: Union[str, Path]) -> bool:
    path = Path(path)
    if path.exists():
        path.unlink()
        if path.exists():
            raise IOError(f"[ODIN] Delete failed: {path}")
    return True