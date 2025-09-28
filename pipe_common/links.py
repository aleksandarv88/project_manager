from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class AssetArtistLink:
    id: int
    asset_id: int
    artist_id: int
    role: Optional[str] = None # optional: the artist's role for this asset
    created_at: Optional[datetime] = None


@dataclass
class AssetShotLink:
    id: int
    asset_id: int
    shot_id: int
    version_used: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AssetTagLink:
    id: int
    asset_id: int
    tag_id: int


@dataclass
class ShotTagLink:
    id: int
    shot_id: int
    tag_id: int