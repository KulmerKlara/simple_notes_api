from uuid import UUID

from fastapi import FastAPI, HTTPException

from IVahit.crud import CreateNoteDef, Crud, CrudElementNotFoundException, FullNoteDef
from IVahit.engines import get_prod_endinge

from ..mylog import getLogger

logger = getLogger(__name__)


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get(path="/note/")
async def notes() -> list[FullNoteDef]:
    crud = Crud(get_prod_endinge())
    return crud.ReadNote()


@app.get(path="/note/{note_id}")
async def note_by_id(note_id: UUID) -> FullNoteDef:
    try:
        crud = Crud(get_prod_endinge())
        notes = crud.ReadNote(note_id)
        return notes[0]
    except CrudElementNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"No Note with id: {e.missing_id}")


@app.post(path="/note/")
async def create_note(note: CreateNoteDef) -> FullNoteDef:
    try:
        crud = Crud(get_prod_endinge())
        return crud.CreateNote(note.note, list(map(lambda x: x.tag, note.tags)))
    except Exception as e:
        logger.error(e)
        raise e







@app.put(path="/note/{note_id}", response_model=FullNoteDef)
async def update_note(note_id: UUID, note: CreateNoteDef):
    try:
        crud = Crud(get_prod_endinge())
        updated_note = crud.UpdateNote(note_id, note.note, [t.tag for t in note.tags])  # pyright: ignore[reportArgumentType]
        if not updated_note:
            raise HTTPException(status_code=404, detail=f"No note found with id {note_id}")
        return updated_note
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete(path="/note/{note_id}")
async def delete_note(note_id: UUID):
    try:
        crud = Crud(get_prod_endinge())
        deleted = crud.DeleteNote(note_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"No note found with id {note_id}")
        return {"message": f"Note {note_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

