from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class TaskInfo:
    id: int
    project_id: int
    artist_id: int
    department_id: int
    task_type: str # e.g. "modeling", "rigging", "sim", "lighting"
    status: str # e.g. "not_started", "in_progress", "review", "done"
    description: Optional[str] = None


    # Scope: tasks can be tied to either an asset or a shot
    asset_id: Optional[int] = None
    shot_id: Optional[int] = None


    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None