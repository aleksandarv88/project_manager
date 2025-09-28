# pipeline_common/context.py
from dataclasses import dataclass
import os
from pipe_common import env_vars

@dataclass
class PipeContext:
    software: str
    task_id: int
    artist_id: int
    project: str
    asset: str
    shot: str

    @classmethod
    def from_env(cls) -> "PipeContext":
        return cls(
            software=os.getenv(env_vars.SOFTWARE, ""),
            task_id=int(os.getenv(env_vars.TASK_ID, "0")),
            artist_id=int(os.getenv(env_vars.ARTIST_ID, "0")),
            project=os.getenv(env_vars.PROJECT, ""),
            asset=os.getenv(env_vars.ASSET, ""),
            shot=os.getenv(env_vars.SHOT, "")
        )
