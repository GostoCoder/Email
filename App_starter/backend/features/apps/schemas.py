from pydantic import BaseModel, HttpUrl


class AppSchema(BaseModel):
    id: str
    name: str
    url: HttpUrl
    description: str
    icon: str
    category: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
