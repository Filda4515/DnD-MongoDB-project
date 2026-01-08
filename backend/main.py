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
    s_count = await spells_collection.count_documents({})
    if s_count == 0:
        spells_seed_data = [
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
        await spells_collection.insert_many(spells_seed_data)
        print("Successfully seeded 5 spells!")
    await spells_collection.create_index([("name", "text"), ("desc", "text")])

    m_count = await monsters_collection.count_documents({})
    if m_count == 0:
        monsters_seed_data = [
            {"name": "Goblin", "hp": 7, "ac": 15, "challenge": "1/4", "desc": "Small humanoids..."},
            {"name": "Mage", "hp": 40, "ac": 12, "challenge": "6", "desc": "A powerful caster..."},
            {"name": "Cultist", "hp": 9, "ac": 12, "challenge": "1/8", "desc": "A fanatic..."},
            {"name": "Acolyte", "hp": 9, "ac": 10, "challenge": "1/4", "desc": "A junior priest..."},
            {"name": "Apprentice", "hp": 15, "ac": 10, "challenge": "1/2", "desc": "Learning magic..."}
        ]
        await monsters_collection.insert_many(monsters_seed_data)
        print("Successfully seeded 5 monsters!")
    await monsters_collection.create_index([("name", "text"), ("desc", "text")])

    yield

app = FastAPI(lifespan=lifespan)

load_dotenv()
MONGO_URL = os.getenv("MONGODB_URL")
client = AsyncMongoClient(MONGO_URL)
db = client.get_database("dnd_database")

spells_collection = db.get_collection("spells")
monsters_collection = db.get_collection("monsters")


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


class MonsterModel(BaseModel):
    id: Optional[Annotated[str, BeforeValidator(str)]] = Field(alias="_id", default=None)
    name: str
    ac: int
    hp: int
    speed: str
    challenge: str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    desc: str

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


@app.get("/status")
def get_status():
    return {"status": "Online", "version": "1.0.0"}


@app.get("/spells", response_model=List[SpellModel])
async def get_all_spells(limit: int = 100):
    return await spells_collection.find().to_list(limit)


@app.get("/spells/{name}", response_model=SpellModel)
async def get_spell(name: str):
    spell = await spells_collection.find_one({"name": name})
    if spell:
        return spell
    raise HTTPException(status_code=404, detail="Spell not found")


@app.get("/search/spells", response_model=List[SpellModel])
async def search_spells(query: str, limit: int = 100):
    return await spells_collection.find({"$text": {"$search": query}}).to_list(limit)


@app.get("/monsters", response_model=List[MonsterModel])
async def get_all_monsters(limit: int = 100):
    return await monsters_collection.find().to_list(limit)


@app.get("/monsters/{name}", response_model=MonsterModel)
async def get_monster(name: str):
    monster = await monsters_collection.find_one({"name": name})
    if monster:
        return monster
    raise HTTPException(status_code=404, detail="Monster not found")


@app.get("/search/monsters", response_model=List[MonsterModel])
async def search_monsters(query: str, limit: int = 100):
    return await monsters_collection.find({"$text": {"$search": query}}).to_list(limit)
