from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.models import Collection, Book, User
from uuid import UUID

class UsersService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, login: str, hashed_password: str) -> Optional[User]:
        existing_user = await self.session.get(User, login)
        if existing_user:
            return None
        new_user = User(login=login, hashed_password=hashed_password)
        self.session.add(new_user)
        await self.session.flush()
        return new_user

    async def get_user(self, login: str) -> Optional[User]:
        return await self.session.get(User, login)

    async def delete_user(self, login: str) -> bool:
        user = await self.session.get(User, login)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.flush()
        return True

class CollectionsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_collection(self, name: str, user_login: str) -> Optional[Collection]:
        user = await self.session.get(User, user_login)
        if not user:
            return None
        collection = Collection(name=name, user_login=user_login)
        self.session.add(collection)
        await self.session.flush()
        return collection

    async def get_collection(self, uuid: UUID) -> Optional[Collection]:
        result = await self.session.execute(
            select(Collection)
            .options(selectinload(Collection.books))
            .where(Collection.uuid == uuid)
        )
        return result.scalar_one_or_none()

    async def update_collection(self, uuid: UUID, new_name: str) -> Optional[Collection]:
        collection = await self.session.get(Collection, uuid)
        if not collection:
            return None
        collection.name = new_name
        await self.session.flush()
        return collection

    async def delete_collection(self, uuid: UUID) -> bool:
        collection = await self.session.get(Collection, uuid)
        if not collection:
            return False
        await self.session.delete(collection)
        await self.session.flush()
        return True

    async def get_user_collections(self, user_login: str) -> List[Collection]:
        result = await self.session.execute(
            select(Collection).where(Collection.user_login == user_login)
        )
        return result.scalars().all()

class BooksService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_book(self, title: str, author: str, description: str, collection_uuid: UUID) -> Optional[Book]:
        collection = await self.session.get(Collection, collection_uuid)
        if not collection:
            return None
        book = Book(title=title, author=author, description=description, collection_uuid=collection_uuid)
        self.session.add(book)
        await self.session.flush()
        return book

    async def get_book(self, uuid: UUID) -> Optional[Book]:
        return await self.session.get(Book, uuid)

    async def update_book(self, uuid: UUID, title: Optional[str] = None, author: Optional[str] = None, description: Optional[str] = None) -> Optional[Book]:
        book = await self.session.get(Book, uuid)
        if not book:
            return None
        if title: book.title = title
        if author: book.author = author
        if description: book.description = description
        await self.session.flush()
        return book

    async def delete_book(self, uuid: UUID) -> bool:
        book = await self.session.get(Book, uuid)
        if not book:
            return False
        await self.session.delete(book)
        await self.session.flush()
        return True

    async def get_collection_books(self, collection_uuid: UUID) -> List[Book]:
        result = await self.session.execute(
            select(Book).where(Book.collection_uuid == collection_uuid)
        )
        return result.scalars().all()

    async def update_file_name(self, book_uuid: UUID, file_name: str) -> Book:
        book = await self.session.get(Book, book_uuid)
        if not book:
            return None
        book.file_name = file_name
        await self.session.flush()
        return book
