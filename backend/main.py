# To run: fastapi dev main.py
import os
from contextlib import asynccontextmanager
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pymongo import AsyncMongoClient
from typing import Annotated, List, Optional


@asynccontextmanager
async def lifespan(app: FastAPI):
    i_count = await items_collection.count_documents({})
    if i_count == 0:
        items_seed_data = [
            {"name": "Iron Sword", "weight": 3.0, "value": "15 gp", "rarity": "Common", "desc": "A sharp blade."},
            {"name": "Wooden Shield", "weight": 5.0, "value": "10 gp", "rarity": "Common", "desc": "Basic protection."},
            {"name": "Healing Potion", "weight": 0.5, "value": "50 gp", "rarity": "Uncommon", "desc": "Restores HP."},
            {"name": "Magic Wand", "weight": 1.0, "value": "500 gp", "rarity": "Rare", "desc": "Channels energy."},
            {"name": "Gold Ring", "weight": 0.1, "value": "25 gp", "rarity": "Common", "desc": "Shiny loot."}
        ]
        await items_collection.insert_many(items_seed_data)
        print("Successfully seeded 5 items!")
    await items_collection.create_index([("name", "text"), ("desc", "text")])

    m_count = await monsters_collection.count_documents({})
    if m_count == 0:
        async def get_item_id(name: str):
            item = await items_collection.find_one({"name": name})
            return item["_id"] if item else None

        monsters_seed_data = [
            {
                "name": "Goblin", 
                "ac": 15, "hp": 7, "speed": "30 ft", "challenge": "1/4",
                "strength": 8, "dexterity": 14, "constitution": 10, "intelligence": 10, "wisdom": 8, "charisma": 8,
                "held_item_id": await get_item_id("Iron Sword"),
                "desc": "Goblins are small, black-hearted, selfish humanoids."
            },
            {
                "name": "Mage", "ac": 12, "hp": 40, "speed": "30 ft", "challenge": "6",
                "strength": 9, "dexterity": 14, "constitution": 11, "intelligence": 17, "wisdom": 12, "charisma": 11,
                "held_item_id": await get_item_id("Magic Wand"),
                "desc": "A powerful spellcaster equipped with arcane knowledge."
            },
            {
                "name": "Cultist", "ac": 12, "hp": 9, "speed": "30 ft", "challenge": "1/8",
                "strength": 11, "dexterity": 12, "constitution": 10, "intelligence": 10, "wisdom": 11, "charisma": 10,
                "held_item_id": await get_item_id("Healing Potion"),
                "desc": "Fanatics who often serve a greater, darker power."
            },
            {
                "name": "Acolyte", "ac": 10, "hp": 9, "speed": "30 ft", "challenge": "1/4",
                "strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "wisdom": 14, "charisma": 11,
                "held_item_id": await get_item_id("Wooden Shield"),
                "desc": "A junior member of a clergy, training in divine arts."
            },
            {
                "name": "Apprentice", "ac": 10, "hp": 15, "speed": "30 ft", "challenge": "1/2",
                "strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 14, "wisdom": 10, "charisma": 11,
                "held_item_id": await get_item_id("Gold Ring"),
                "desc": "A novice wizard still mastering the basics of magic."
            }
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

items_collection = db.get_collection("items")
monsters_collection = db.get_collection("monsters")

PyObjectId = Annotated[str, BeforeValidator(str)]


class ItemModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    weight: float
    value: str
    rarity: str
    desc: str

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class MonsterModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
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
    held_item_id: Optional[PyObjectId] = Field(default=None)
    desc: str

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


@app.get("/status")
def get_status():
    return {"status": "Online", "version": "1.0.0"}


@app.get("/items", response_model=List[ItemModel])
async def get_all_spells(limit: int = 100):
    return await items_collection.find().to_list(limit)


@app.get("/items/{item_id}", response_model=ItemModel)
async def get_item_by_id(item_id: str):
    item = await items_collection.find_one({"_id": ObjectId(item_id)})
    if item:
        return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/search/items", response_model=List[ItemModel])
async def search_items(query: str, limit: int = 100):
    return await items_collection.find({"$text": {"$search": query}}).to_list(limit)


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
