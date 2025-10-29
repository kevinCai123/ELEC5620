from __future__ import annotations

import uuid


def generate_plan_item_uid(plan_id: int, item_id: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"plan:{plan_id}:item:{item_id}"))


__all__ = ["generate_plan_item_uid"]
