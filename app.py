import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app = FastAPI()
# app.mount("/chat", StaticFiles(directory="./templates/", html=True), name="html")

MONGODB_URL="mongodb://127.0.0.1/?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
# client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.honya


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")
# 第一引数はデフォルト値, 省略（...）時は必須になる
class FileRecordModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str = Field(...)
    text: str = Field(...)
    file_format: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "hoge_file",
                "text": "これはファイル本文です",
                "file_format": "pdf",
            }
        }


class UpdateFileRecordModel(BaseModel):
    title: Optional[str]
    text: Optional[str]
    file_foramt: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "update_hoge_file",
                "text": "これは更新用ファイル本文です",
                "file_format": "pdf",
            }
        }


@app.post("/", response_description="Add new FileRecord", response_model=FileRecordModel)
async def create_student(filerecord : FileRecordModel = Body(...)):
    filerecord = jsonable_encoder(filerecord )
    new_filerecord  = await db["FileRecord"].insert_one(filerecord )
    created_student = await db["FileRecord"].find_one({"_id": new_filerecord .inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_student)

@app.get(
    "/", response_description="List all file", response_model=List[FileRecordModel]
)
async def list_students():
    students = await db["FileRecord"].find().to_list(1000)
    return students


@app.get(
    "/{id}", response_description="Get a single file", response_model=FileRecordModel
)
async def show_student(id: str):
    if (file := await db["FileRecord"].find_one({"_id": id})) is not None:
        return file

    raise HTTPException(status_code=404, detail=f"File {id} not found")


@app.put("/{id}", response_description="Update a FileRecord", response_model=FileRecordModel)
async def update_student(id: str, student: UpdateFileRecordModel = Body(...)):
    files = {k: v for k, v in student.dict().items() if v is not None}
    print(files)

    if len(files) >= 1:
        update_result = await db["FileRecord"].update_one({"_id": id}, {"$set": files})

        if update_result.modified_count == 1:
            if (
                updated_file := await db["FileRecord"].find_one({"_id": id})
            ) is not None:
                return updated_file

    if (existing_file := await db["FileRecord"].find_one({"_id": id})) is not None:
        return existing_file

    raise HTTPException(status_code=404, detail=f"FileRecord {id} not found")


@app.delete("/{id}", response_description="Delete a file")
async def delete_student(id: str):
    delete_result = await db["FileRecord"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        # return Response(status_code=status.HTTP_204_NO_CONTENT)
        return {"answer":"ここか","respon":Response(status_code=status.HTTP_204_NO_CONTENT)}

    raise HTTPException(status_code=404, detail=f"Student {id} not found")
