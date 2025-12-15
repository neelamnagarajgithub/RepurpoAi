# Backend/src/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationOut(BaseModel):
    id: UUID
    user_id: int
    title: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class MessageCreate(BaseModel):
    conversation_id: Optional[UUID] = None
    role: Optional[str] = "user"
    content: str
    meta: Optional[Any] = None

class MessageOut(BaseModel):
    id: int
    user_id: int
    conversation_id: UUID
    role: str
    content: str
    meta: Optional[Any] = None
    created_at: datetime

    class Config:
        orm_mode = True

class DownloadCreate(BaseModel):
    filename: str
    url: str
    meta: Optional[Any] = None

class DownloadOut(BaseModel):
    id: int
    user_id: int
    filename: str
    url: str
    meta: Optional[Any] = None
    created_at: datetime

    class Config:
        orm_mode = True