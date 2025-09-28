from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class ProjectInfo:
    id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None # e.g. "active", "archived"