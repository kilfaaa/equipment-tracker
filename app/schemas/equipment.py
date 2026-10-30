from pydantic import BaseModel, ConfigDict, Field, field_validator


class EquipmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    inventory_number: str = Field(min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("inventory_number", mode="before")
    @classmethod
    def normalize_inventory_number(cls, value):
        if isinstance(value, str):
            return value.strip().upper()
        return value


class EquipmentRead(BaseModel):
    id: int
    name: str
    inventory_number: str