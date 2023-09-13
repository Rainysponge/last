from typing import List, Dict, Union, Optional
from pydantic import BaseModel
from enum import Enum, auto
from datetime import datetime
import uuid
from enum import Enum


class RiskDimension(BaseModel):
    level: Optional[int]
    name: str
    description: Optional[str]

    def __str__(self):
        return self.name


RelatedRiskDimensions = Dict[str, Dict[str, Dict[str, str]]]


class PermissionLevel(Enum):
    SUPER_ADMIN = auto()
    ADMIN = auto()
    EDITOR = auto()
    OPERATOR = auto()
    VIEWER = auto()



class DateString(BaseModel):
    year: str
    month: str
    day: str
    hour: str
    minute: str
    second: str

    def to_datetime(self):
        return datetime.strptime(self.__str__, "%Y-%m-%d %H:%M:%S")

    def format(self, format_str):
        date_obj = self.to_datetime()
        return date_obj.strftime(format_str)

    def __str__(self):
        return f"{self.year}-{self.month}-{self.day} {self.hour}:{self.minute}:{self.second}"


class UserInfo(BaseModel):
    id: str
    name: str
    email: str
    created_at: DateString  
    permission: PermissionLevel


class CodeMsg(BaseModel):
    code: int
    message: str

    def __str__(self):
        return f"Error {self.code}: {self.message}"

class ReturnCode(Enum):
    NOT_FOUND = CodeMsg(code=404, message="Not found")
    UNAUTHORIZED = CodeMsg(code=401, message="Unauthorized")
    FORBIDDEN = CodeMsg(code=403, message="Forbidden")
    SUCCESS = CodeMsg(code=10000, message="Success")
    BAD_REQUEST = CodeMsg(code=400, message="Bad Request")
    INVALID_INPUT = CodeMsg(code=422, message="Invalid Input")

    def __str__(self):
        return str(self.value)

class StateCode(Enum):
    In_Progress = CodeMsg(code=0, message="进行中")
    Done = CodeMsg(code=1, message="已完成")
    Error = CodeMsg(code=-1, message="异常")

    def __str__(self):
        return str(self.value)


class ID:
    def __init__(self):
        self.id = str(uuid.uuid4())