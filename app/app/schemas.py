from pydantic import BaseModel, ConfigDict, Field
from typing import List
from uuid import UUID

# --- USERS ---
class UserCreate(BaseModel):
    login: str = Field(..., example="user1")
    password: str = Field(..., example="super_secret_password")

class UserRead(BaseModel):
    login: str
    model_config = ConfigDict(from_attributes=True)

# --- COLLECTIONS ---
class CollectionCreate(BaseModel):
    name: str = Field(..., example="My Books")

class CollectionRead(BaseModel):
    uuid: UUID
    name: str
    user_login: str
    model_config = ConfigDict(from_attributes=True)

class CollectionReadWithBooks(CollectionRead):
    books: List["BookRead"] = []

# --- BOOKS ---
class BookCreate(BaseModel):
    title: str = Field(..., example="War and Peace")
    author: str = Field(..., example="Leo Tolstoy")
    description: str = Field(..., example="A classic novel.")

class BookRead(BaseModel):
    uuid: UUID
    title: str
    author: str
    description: str
    file_name: str | None
    collection_uuid: UUID
    model_config = ConfigDict(from_attributes=True)

CollectionReadWithBooks.model_rebuild()
