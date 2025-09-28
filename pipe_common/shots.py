from dataclasses import dataclass
from typing import Optional


@dataclass
class ShotInfo:
    id: int
    sequence_id: int
    project_id: int # denormalized convenience; can be derived via Sequence
    name: str # e.g. "sh010"
    frame_start: Optional[int] = None
    frame_end: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None