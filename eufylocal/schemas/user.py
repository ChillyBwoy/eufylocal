from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    color: str = Field(min_length=1)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    color: str | None = Field(default=None, min_length=1)


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
