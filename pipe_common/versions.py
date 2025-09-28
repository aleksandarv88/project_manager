from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class VersionInfo:
    id: int
    asset_id: int # or make shot_id Optional[int] if you version shots too
    version_number: str # e.g. "v001"
    file_path: str
    thumbnail: Optional[str] = None
    status: Optional[str] = None # e.g. "wip", "approved"
    artist_id: Optional[int] = None
    created_at: Optional[datetime] = None

