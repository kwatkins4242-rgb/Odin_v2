# orchestrator/priority_queue.py
"""
Tiny priority queue for concurrent user requests.
Lower number = higher priority.
"""

import heapq
import uuid
from typing import Callable, Dict, Any
from dataclasses import dataclass, field

@dataclass(order=True)
class Task:
    priority: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = field(compare=False)
    callback: Callable = field(compare=False)

class PriorityQueue:
    def __init__(self):
        self._q = []

    def push(self, payload: Dict[str, Any], callback: Callable, priority: int = 5):
        heapq.heappush(self._q, Task(priority, payload=payload, callback=callback))

    def pop(self) -> Task | None:
        return heapq.heappop(self._q) if self._q else None

    def empty(self) -> bool:
        return not self._q