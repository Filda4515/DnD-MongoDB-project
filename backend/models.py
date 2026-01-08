from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from typing import Annotated, Optional

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
