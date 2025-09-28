from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class AssetTypeInfo:
    id: int
    name: str # e.g. "prop", "character", "environment", "fx"
    description: Optional[str] = None


@dataclass
class AssetInfo:
    id: int
    project_id: int
    asset_type_id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None # e.g. "wip", "approved", "published"
    version: Optional[str] = None # current version label like "v003"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    thumbnail: Optional[str] = None # path/URL
    artist_ids: Optional[List[int]] = None # convenience for DTOs (DB uses join table)


    # Shot-specific usage: keep core Asset general; link to shots via AssetShotLink.

