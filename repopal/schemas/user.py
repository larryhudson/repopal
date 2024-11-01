from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
