from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Engine, Select, select
from sqlalchemy.orm import Session

from IVahit.model._model import Note, Tag
from IVahit.mylog import getLogger

logger = getLogger(__name__)


class CreateTagDef(BaseModel):
    tag: str


class FullTagDef(CreateTagDef):
    id: UUID
    note_id: UUID


class BaseNoteDef(BaseModel):
    note: str


class CreateNoteDef(BaseNoteDef):
    note: str
    tags: list[CreateTagDef]


class FullNoteDef(BaseNoteDef):
    id: UUID
    tags: list[FullTagDef]


class CrudElementNotFoundException(Exception):
    def __init__(self, missing_id: UUID):
        super().__init__(f"No element with id {missing_id}")
        self._missing_id: UUID = missing_id

    @property
    def missing_id(self):
        return self._missing_id


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


    def DeleteNote(self, note_id: int) -> bool:
        logger.debug("Delete note {note_id}")
        with Session(self._engine) as session:
            note = session.get(Note, note_id)
            if not note:
                logger.debug("Note not found for deletion")
                return False

            session.delete(note)
            session.commit()
            logger.debug("Note deleted")
            return True

            

 