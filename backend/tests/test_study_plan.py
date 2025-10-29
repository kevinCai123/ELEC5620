from __future__ import annotations

from app.services.study import generate_plan_item_uid


def test_plan_item_uid_idempotent() -> None:
    uid_one = generate_plan_item_uid(1, 42)
    uid_two = generate_plan_item_uid(1, 42)
    assert uid_one == uid_two
    assert uid_one == "59ccdc4f-f0da-50fc-8ddb-6e4eaaaf043a"
