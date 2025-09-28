from dataclasses import dataclass
from typing import Optional


@dataclass
class SequenceInfo:
    id: int
    project_id: int
    name: str
    description: Optional[str] = None