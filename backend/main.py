# To run: fastapi dev main.py
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pymongo import AsyncMongoClient
from typing import Annotated, List, Optional


@asynccontextmanager
async def lifespan(app: FastAPI):
    count = await spells_collection.count_documents({})

    if count == 0:
        test_data = [
            {
                "name": "Acid Arrow", "level": 2, "school": "Evocation", "casting_time": "1 action",
                "range": "90 feet", "duration": "Instantaneous", "components": ["V", "S", "M"], "concentration": False,
                "desc": "A shimmering green arrow..."
            },
            {
                "name": "Detect Magic", "level": 1, "school": "Divination", "casting_time": "1 action",
                "range": "Self", "duration": "10 min", "components": ["V", "S"], "concentration": True,
                "desc": "For the duration..."
            },
            {
                "name": "Fireball", "level": 3, "school": "Evocation", "casting_time": "1 action",
                "range": "150 feet", "duration": "Instantaneous", "components": ["V", "S", "M"], "concentration": False,
                "desc": "A bright streak flashes..."
            },
            {
                "name": "Shield", "level": 1, "school": "Abjuration", "casting_time": "1 reaction", "range": "Self",
                "duration": "1 round", "components": ["V", "S"], "concentration": False,
                "desc": "An invisible barrier..."
            },
            {
                "name": "Misty Step", "level": 2, "school": "Conjuration", "casting_time": "1 bonus action",
                "range": "Self", "duration": "Instantaneous", "components": ["V"], "concentration": False,
                "desc": "Briefly surrounded..."
            }
        ]
        await spells_collection.insert_many(test_data)
        print("Successfully seeded 5 spells into Atlas!")

    await spells_collection.create_index([("name", "text"), ("desc", "text")])

    yield

app = FastAPI(lifespan=lifespan)

load_dotenv()
MONGO_URL = os.getenv("MONGODB_URL")
client = AsyncMongoClient(MONGO_URL)
db = client.get_database("dnd_database")
spells_collection = db.get_collection("spells")


class SpellModel(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default=None)
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    duration: str
    components: List[str]
    concentration: bool
    desc: str

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


@app.get("/status")
def get_status():
    return {"status": "Online", "version": "1.0.0"}


@app.get("/spells", response_model=List[SpellModel])
async def get_all_spells():
    return await spells_collection.find().to_list(100)


@app.get("/spells/{name}", response_model=SpellModel)
async def get_spell(name: str):
    spell = await spells_collection.find_one({"name": name})
    if spell:
        return spell
    raise HTTPException(status_code=404, detail="Spell not found")
