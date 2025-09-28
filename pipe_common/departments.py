from dataclasses import dataclass
from typing import Optional


@dataclass
class DepartmentInfo:
    id: int
    name: str
    description: Optional[str] = None
