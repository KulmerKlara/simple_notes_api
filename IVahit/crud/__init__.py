from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, Select, select
from sqlalchemy.orm import Session

from IVahit.model._model import Note, Tag, Group
from IVahit.mylog import getLogger

logger = getLogger(__name__)


# ------------------- Tag Models -------------------

class CreateTagDef(BaseModel):
    tag: str


class FullTagDef(CreateTagDef):
    id: UUID
    note_id: UUID


# ------------------- Note Models -------------------

class BaseNoteDef(BaseModel):
    note: str


class CreateNoteDef(BaseNoteDef):
    note: str
    tags: list[CreateTagDef]


class FullNoteDef(BaseNoteDef):
    id: UUID
    tags: list[FullTagDef]


# ------------------- Exception -------------------

class CrudElementNotFoundException(Exception):
    def __init__(self, missing_id: UUID):
        super().__init__(f"No element with id {missing_id}")
        self._missing_id: UUID = missing_id

    @property
    def missing_id(self):
        return self._missing_id


# ------------------- Note CRUD -------------------

class Crud:
    def __init__(self, engine: Engine):
        self._engine: Engine = engine

    def ReadNote(self, id: None | UUID = None):
        logger.debug("ReadNote: Start")
        with Session(self._engine) as session:
            logger.debug("ReadNote: Session")
            stmt: Select[tuple[Note]] = select(Note)
            if id:
                stmt = stmt.where(Note.id == id)
            logger.debug("ReadNote: Try to get notes")
            notes = session.scalars(stmt)
            logger.debug("ReadNote: Got notes")
            logger.debug(notes)
            notes = list(
                map(
                    lambda x: FullNoteDef(
                        id=x.id,
                        note=x.note,
                        tags=list(
                            map(
                                lambda y: FullTagDef(
                                    tag=y.tag, id=y.id, note_id=y.note_id
                                ),
                                x.tags,
                            )
                        ),
                    ),
                    notes,
                )
            )
            if id and not notes:
                raise CrudElementNotFoundException(id)
            logger.debug("ReadNote: Converted notes %s", notes)

            return notes

    def CreateNote(self, note: str, tags: list[str] | None = None):
        logger.debug("Create a note")
        with Session(self._engine) as session:
            note_element = Note()
            note_element.note = note
            session.add(note_element)
            logger.debug("adding tags")
            if tags:
                for single_tag in tags:
                    tag = Tag()
                    tag.tag = single_tag
                    tag.note = note_element
                    session.add(tag)
            logger.debug("Try to commit")
            session.commit()
            logger.debug("Created a note")
            return FullNoteDef(
                id=note_element.id,
                note=note_element.note,
                tags=list(
                    map(
                        lambda x: FullTagDef(id=x.id, note_id=x.note_id, tag=x.tag),
                        note_element.tags,
                    )
                ),
            )

    def UpdateNote(self, note_id: int, new_text: str | None = None, new_tags: list[str] | None = None) -> FullNoteDef | None:
        logger.debug("Update note {note_id}")
        with Session(self._engine) as session:
            note = session.get(Note, note_id)
            if not note:
                logger.debug("Note not found for update")
                return None

            if new_text:
                note.note = new_text
            if new_tags is not None:
                for old_tag in note.tags:
                    session.delete(old_tag)
                for tag_text in new_tags:
                    tag = Tag(tag=tag_text, note=note)
                    session.add(tag)

            session.commit()
            logger.debug("Note updated")

            return FullNoteDef(
                id=note.id,
                note=note.note,
                tags=[
                    FullTagDef(id=t.id, note_id=t.note_id, tag=t.tag)
                    for t in note.tags
                ],
            )

    def DeleteNote(self, note_id: UUID) -> bool:
        logger.debug(f"Delete note {note_id}")
        with Session(self._engine) as session:
            note = session.get(Note, note_id)
            if not note:
                logger.debug("Note not found for deletion")
                return False
            session.delete(note)
            session.commit()
            logger.debug("Note deleted")
            return True




class CreateGroupDef(BaseModel):
    name: str


class FullGroupDef(CreateGroupDef):
    id: UUID
    note_ids: list[UUID] = []


class CrudGroups:
    def __init__(self, engine):
        self._engine = engine

    def CreateGroup(self, name: str, note_ids: list[UUID] | None = None) -> FullGroupDef:
        with Session(self._engine) as session:
            group = Group(name=name)
            session.add(group)
            if note_ids:
                for note_id in note_ids:
                    note = session.get(Note, note_id)
                    if note:
                        note.group = group
            session.commit()
            return FullGroupDef(
                id=group.id,
                name=group.name,
                note_ids=[note.id for note in group.notes]
            )

    def ReadGroup(self, id: UUID | None = None) -> list[FullGroupDef]:
        with Session(self._engine) as session:
            stmt = select(Group)
            if id:
                stmt = stmt.where(Group.id == id)
            groups = session.scalars(stmt).all()
            return [
                FullGroupDef(
                    id=g.id,
                    name=g.name,
                    note_ids=[n.id for n in g.notes]
                )
                for g in groups
            ]

    def UpdateGroup(self, group_id: UUID, new_name: str | None = None, new_note_ids: list[UUID] | None = None) -> FullGroupDef | None:
        with Session(self._engine) as session:
            group = session.get(Group, group_id)
            if not group:
                return None
            if new_name:
                group.name = new_name
            if new_note_ids is not None:
                # Alte Notes entfernen
                for note in group.notes:
                    note.group = None
                # Neue Notes zuordnen
                for note_id in new_note_ids:
                    note = session.get(Note, note_id)
                    if note:
                        note.group = group
            session.commit()
            return FullGroupDef(
                id=group.id,
                name=group.name,
                note_ids=[n.id for n in group.notes]
            )

    def DeleteGroup(self, group_id: UUID) -> bool:
        with Session(self._engine) as session:
            group = session.get(Group, group_id)
            if not group:
                return False
            for note in group.notes:
                note.group = None
            session.delete(group)
            session.commit()
            return True
