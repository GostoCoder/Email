from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_serializer


class AppSchema(BaseModel):
    id: str
    name: str
    url: HttpUrl
    description: str
    icon: str
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    class Config:
        from_attributes = True
