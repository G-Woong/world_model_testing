"""RG-4F (RegimeGrid-4Room Factorized Tasks) 환경.

외부에서 가장 자주 import되는 객체를 re-export한다.
    - ``RG4FEnv``  : 메인 환경 클래스
    - ``RG4FConfig``: 모든 수치를 모은 dataclass
    - ``Action`` 등 enum

dataset generator, model, planner는 본 모듈에 포함되지 않는다 (Session 3+ 책임).
"""
from .config import RG4FConfig
from .env import RG4FEnv
from .types import (
    Action,
    ControlMode,
    EventToken,
    FieldFamily,
    MOVE_ACTIONS,
    MobilityMode,
    Position,
    RoomID,
    StateDim,
    TaskID,
    TargetBandInfo,
)

__all__ = [
    "RG4FEnv",
    "RG4FConfig",
    "Action",
    "ControlMode",
    "EventToken",
    "FieldFamily",
    "MOVE_ACTIONS",
    "MobilityMode",
    "Position",
    "RoomID",
    "StateDim",
    "TaskID",
    "TargetBandInfo",
]
