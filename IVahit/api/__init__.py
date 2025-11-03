from uuid import UUID
from typing import List

from fastapi import FastAPI, HTTPException

from IVahit.crud import (
    CreateNoteDef,
    Crud,
    CrudElementNotFoundException,
    FullNoteDef,
    CrudGroups,
    FullGroupDef
)
from IVahit.engines import get_prod_endinge

from ..mylog import getLogger

logger = getLogger(__name__)

app = FastAPI()

# ------------------- Root -------------------
@app.get("/")
async def root():
    return {"message": "Hello World!"}


# ------------------- Note Endpoints -------------------
@app.get("/note/", response_model=list[FullNoteDef])
async def notes() -> list[FullNoteDef]:
    crud = Crud(get_prod_endinge())
    return crud.ReadNote()


@app.get("/note/{note_id}", response_model=FullNoteDef)
async def note_by_id(note_id: UUID) -> FullNoteDef:
    try:
        crud = Crud(get_prod_endinge())
        notes = crud.ReadNote(note_id)
        return notes[0]
    except CrudElementNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"No Note with id: {e.missing_id}")


@app.post("/note/", response_model=FullNoteDef)
async def create_note(note: CreateNoteDef) -> FullNoteDef:
    try:
        crud = Crud(get_prod_endinge())
        return crud.CreateNote(note.note, [t.tag for t in note.tags])
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
 
 

@app.delete("/note/{note_id}")
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


# ------------------- Group Endpoints -------------------
crud_groups = CrudGroups(get_prod_endinge())

@app.post("/groups/", response_model=FullGroupDef)
def create_group(name: str, note_ids: List[UUID] = []):
    return crud_groups.CreateGroup(name=name, note_ids=note_ids)


@app.get("/groups/", response_model=List[FullGroupDef])
def read_groups():
    return crud_groups.ReadGroup()


@app.get("/groups/{group_id}", response_model=FullGroupDef)
def read_group(group_id: UUID):
    group = crud_groups.ReadGroup(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group[0]


@app.put("/groups/{group_id}", response_model=FullGroupDef)
def update_group(group_id: UUID, new_name: str | None = None, new_note_ids: List[UUID] | None = None):
    group = crud_groups.UpdateGroup(group_id, new_name=new_name, new_note_ids=new_note_ids)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@app.delete("/groups/{group_id}", response_model=bool)
def delete_group(group_id: UUID):
    success = crud_groups.DeleteGroup(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return success
