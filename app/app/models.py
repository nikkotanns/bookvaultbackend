from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    login: Mapped[str] = mapped_column(String(255), primary_key=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    collections: Mapped[list["Collection"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Collection(Base):
    __tablename__ = "collections"
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_login: Mapped[str] = mapped_column(
        ForeignKey("users.login", ondelete="CASCADE"),
        nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="collections")
    books: Mapped[list["Book"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class Book(Base):
    __tablename__ = "books"
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    collection_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("collections.uuid", ondelete="CASCADE"),
        nullable=False
    )
    collection: Mapped["Collection"] = relationship(back_populates="books")
