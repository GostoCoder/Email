from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass
class AppModel:
    id: str
    name: str
    url: str
    description: str
    icon: str
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


SAMPLE_APPS = [
    AppModel(
        id=str(uuid4()),
        name="Demo Template",
        url="https://app-starter.reception.local",
        description="Starter app aligned with Hub-Almadia standards.",
        icon="🚀",
        category="templates",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
]
