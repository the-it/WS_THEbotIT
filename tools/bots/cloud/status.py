from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict, Any, Dict, Optional, Union


# typehints
class StatusDictType(TypedDict):
    id: int
    bot_name: str
    success: bool
    finish: bool
    start_time: str
    finish_time: str
    output: Optional[Dict[str, Union[int, str, bool]]]


@dataclass
class Status:
    id: int
    bot_name: str
    success: bool = False
    finish: bool = False
    start_time: datetime = datetime.min
    finish_time: datetime = datetime.min
    output: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.start_time == datetime.min:
            self.start_time = datetime.now()

    @classmethod
    def from_dict(cls, class_dict):
        for key in class_dict:
            if key.find("time") != -1:
                class_dict[key] = datetime.fromisoformat(class_dict[key])
        return Status(**class_dict)

    def to_dict(self) -> StatusDictType:
        return_dict: StatusDictType = {
            "id": self.id,
            "bot_name": self.bot_name,
            "success": self.success,
            "finish": self.finish,
            "start_time": self.start_time.isoformat(),
            "finish_time": self.finish_time.isoformat(),
            "output": self.output
        }
        return return_dict

    def close_run(self, success: bool, finish: bool) -> StatusDictType:
        self.finish_time = datetime.now()
        self.success = success
        self.finish = finish
        return self.to_dict()
