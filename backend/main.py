# To run: fastapi dev main.py
import os
from bson import ObjectId
from bson.errors import InvalidId
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pymongo import AsyncMongoClient
from typing import List

from models import ItemModel, MonsterModel


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
                "name": "Goblin", "ac": 15, "hp": 7, "speed": "30 ft", "challenge": "1/4",
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

version = "1.0.0"
app = FastAPI(lifespan=lifespan, version=version)

load_dotenv()
MONGO_URL = os.getenv("MONGODB_URL")
client = AsyncMongoClient(MONGO_URL)
db = client.get_database("dnd_database")

items_collection = db.get_collection("items")
monsters_collection = db.get_collection("monsters")


@app.get("/status")
def get_status():
    return {"status": "Online", "version": version}


@app.get("/items", response_model=List[ItemModel], tags=["Items"])
async def get_all_items(limit: int = 100):
    return await items_collection.find().to_list(limit)


@app.get("/items/{item_id}", response_model=ItemModel, tags=["Items"])
async def get_item(item_id: str):
    try:
        obj_id = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    item = await items_collection.find_one({"_id": obj_id})
    if item:
        return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/search/items", response_model=List[ItemModel], tags=["Items"])
async def search_items(query: str, limit: int = 100):
    return await items_collection.find({"$text": {"$search": query}}).to_list(limit)


@app.post("/items", response_model=ItemModel, status_code=201, tags=["Items"])
async def create_item(item: ItemModel):
    item_dict = item.model_dump(by_alias=True, exclude={"id"})

    existing = await items_collection.find_one({"name": item.name})
    if existing:
        raise HTTPException(status_code=400, detail="Item already exists")

    result = await items_collection.insert_one(item_dict)

    new_item = await items_collection.find_one({"_id": result.inserted_id})
    return new_item


@app.delete("/items/{item_id}", tags=["Items"])
async def delete_item(item_id: str):
    try:
        obj_id = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    delete_result = await items_collection.delete_one({"_id": obj_id})

    if delete_result.deleted_count == 1:
        return {"message": "Item successfully deleted"}

    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/monsters", response_model=List[MonsterModel], tags=["Monsters"])
async def get_all_monsters(limit: int = 100):
    return await monsters_collection.find().to_list(limit)


@app.get("/monsters/{name}", response_model=MonsterModel, tags=["Monsters"])
async def get_monster(name: str):
    monster = await monsters_collection.find_one({"name": name})
    if monster:
        return monster
    raise HTTPException(status_code=404, detail="Monster not found")


@app.get("/search/monsters", response_model=List[MonsterModel], tags=["Monsters"])
async def search_monsters(query: str, limit: int = 100):
    return await monsters_collection.find({"$text": {"$search": query}}).to_list(limit)


@app.post("/monsters", response_model=MonsterModel, status_code=201, tags=["Monsters"])
async def create_monster(monster: MonsterModel):
    monster_dict = monster.model_dump(by_alias=True, exclude={"id"})

    existing = await monsters_collection.find_one({"name": monster.name})
    if existing:
        raise HTTPException(status_code=400, detail="Monster already exists")

    if monster.held_item_id:
        item_exists = await items_collection.find_one({"_id": ObjectId(monster.held_item_id)})
        if not item_exists:
            raise HTTPException(status_code=400, detail="The specified held_item_id does not exist")

    result = await monsters_collection.insert_one(monster_dict)

    new_monster = await monsters_collection.find_one({"_id": result.inserted_id})
    return new_monster


@app.delete("/monsters/{monster_id}", tags=["Monsters"])
async def delete_monster(monster_id: str):
    delete_result = await monsters_collection.delete_one({"_id": ObjectId(monster_id)})

    if delete_result.deleted_count == 1:
        return {"message": "Monster successfully deleted"}

    raise HTTPException(status_code=404, detail="Monster not found")
