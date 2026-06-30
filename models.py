from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass
class CheckResult:
    site: str
    available: bool
    url: str
    price: Optional[float] = None
    message: str = ""
    error: bool = False


@dataclass
class PhysicalProduct:
    name: str
    search_term: str
    sites: List[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    max_price: Optional[float] = None

    def to_dict(self):
        return {
            "id": self.id,
            "type": "physical",
            "name": self.name,
            "search_term": self.search_term,
            "sites": self.sites,
            "max_price": self.max_price,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            name=d["name"],
            search_term=d["search_term"],
            sites=d["sites"],
            max_price=d.get("max_price"),
        )


@dataclass
class EventProduct:
    name: str
    search_term: str
    sites: List[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    max_price: Optional[float] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.id,
            "type": "event",
            "name": self.name,
            "search_term": self.search_term,
            "sites": self.sites,
            "max_price": self.max_price,
            "date_start": self.date_start,
            "date_end": self.date_end,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            id=d["id"],
            name=d["name"],
            search_term=d["search_term"],
            sites=d["sites"],
            max_price=d.get("max_price"),
            date_start=d.get("date_start"),
            date_end=d.get("date_end"),
        )
