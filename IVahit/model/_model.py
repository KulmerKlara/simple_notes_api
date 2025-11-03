from typing import List, Optional, TYPE_CHECKING, override
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from __main__ import Note 


class Base(DeclarativeBase):
    pass


class Note(Base):
    __tablename__ = "note"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    note: Mapped[str] = mapped_column(String(1000))

    tags: Mapped[List["Tag"]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )

    group_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("group.id"), nullable=True)
    group: Mapped[Optional["Group"]] = relationship(back_populates="notes")

    @override
    def __repr__(self) -> str:
        return f"Note(id={self.id!r}, note={self.note!r})"

class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    note_id: Mapped[UUID] = mapped_column(ForeignKey("note.id"))
    note: Mapped["Note"] = relationship(back_populates="tags")
    tag: Mapped[str] = mapped_column(String(30))

    @override
    def __repr__(self) -> str:
        return f"Tag(id={self.id!r}, note_id={self.note_id!r}, note={self.note.note!r}, tag={self.tag!r})"

class Group(Base):
    __tablename__ = "group"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    notes: Mapped[List[Note]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    @override
    def __repr__(self) -> str:
        return f"Group(id={self.id!r}, name={self.name!r}, notes={len(self.notes)})"
