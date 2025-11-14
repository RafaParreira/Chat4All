from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    room_id: int
    sender_id: int
    content: str


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
