import json
import os
from typing import List, Union

from models import EventProduct, PhysicalProduct

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "products.json")


def _default_config():
    return {"physical": [], "events": []}


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return _default_config()
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def get_products() -> List[Union[PhysicalProduct, EventProduct]]:
    cfg = load_config()
    products = []
    for p in cfg.get("physical", []):
        products.append(PhysicalProduct.from_dict(p))
    for e in cfg.get("events", []):
        products.append(EventProduct.from_dict(e))
    return products


def add_product(product: Union[PhysicalProduct, EventProduct]):
    cfg = load_config()
    if isinstance(product, PhysicalProduct):
        cfg.setdefault("physical", []).append(product.to_dict())
    else:
        cfg.setdefault("events", []).append(product.to_dict())
    save_config(cfg)


def remove_product(product_id: str) -> bool:
    cfg = load_config()
    before = sum(len(v) for v in cfg.values())
    cfg["physical"] = [p for p in cfg.get("physical", []) if p["id"] != product_id]
    cfg["events"] = [e for e in cfg.get("events", []) if e["id"] != product_id]
    after = sum(len(v) for v in cfg.values())
    if after < before:
        save_config(cfg)
        return True
    return False
