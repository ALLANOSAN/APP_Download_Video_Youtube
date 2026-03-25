from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = Field(default=True)

    history: List["HistoryItem"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class HistoryItemBase(SQLModel):
    video_id: str
    title: str
    url: str
    thumbnail: Optional[str] = None
    uploader: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HistoryItem(HistoryItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    user: User = Relationship(back_populates="history")

class HistoryItemCreate(HistoryItemBase):
    pass
