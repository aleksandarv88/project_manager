from dataclasses import dataclass
from typing import Optional


@dataclass
class ArtistInfo:
    id: int
    name: str
    email: str
    department_id: int
    role: Optional[str] = None