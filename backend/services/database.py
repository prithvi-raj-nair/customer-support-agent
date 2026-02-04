import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import uuid

from backend.config import DATA_DIR
from backend.models.schemas import User, Order, HumanQueueItem, EmailInput, EmailResponse


def load_json(filename: str) -> dict:
    filepath = DATA_DIR / filename
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filename: str, data: dict) -> None:
    filepath = DATA_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# User operations
def get_all_users() -> list[User]:
    data = load_json("users.json")
    return [User(**u) for u in data["users"]]


def get_user_by_email(email: str) -> Optional[User]:
    data = load_json("users.json")
    for u in data["users"]:
        if u["email"].lower() == email.lower():
            return User(**u)
    return None


# Order operations
def get_all_orders() -> list[Order]:
    data = load_json("orders.json")
    return [Order(**o) for o in data["orders"]]


def get_orders_for_user(user_id: str, days: int = 14) -> list[Order]:
    data = load_json("orders.json")
    cutoff = datetime.utcnow() - timedelta(days=days)

    orders = []
    for o in data["orders"]:
        if o["user_id"] == user_id:
            order_date = datetime.fromisoformat(o["order_date"].replace("Z", "+00:00"))
            if order_date.replace(tzinfo=None) >= cutoff:
                orders.append(Order(**o))

    return sorted(orders, key=lambda x: x.order_date, reverse=True)


def get_order_by_id(order_id: str) -> Optional[Order]:
    data = load_json("orders.json")
    for o in data["orders"]:
        if o["order_id"] == order_id:
            return Order(**o)
    return None


# Human queue operations
def get_human_queue() -> list[HumanQueueItem]:
    data = load_json("human_queue.json")
    return [HumanQueueItem(**item) for item in data["queue"]]


def add_to_human_queue(email_input: EmailInput, reason: str) -> HumanQueueItem:
    data = load_json("human_queue.json")

    item = HumanQueueItem(
        id=str(uuid.uuid4()),
        email_input=email_input,
        reason=reason,
        timestamp=datetime.utcnow().isoformat() + "Z",
        resolved=False
    )

    data["queue"].append(item.model_dump())
    save_json("human_queue.json", data)

    return item


def resolve_queue_item(item_id: str) -> bool:
    data = load_json("human_queue.json")

    for item in data["queue"]:
        if item["id"] == item_id:
            item["resolved"] = True
            save_json("human_queue.json", data)
            return True

    return False


# Sent emails operations
def get_sent_emails() -> list[EmailResponse]:
    data = load_json("sent_emails.json")
    return [EmailResponse(**e) for e in data["emails"]]


def save_sent_email(email: EmailResponse) -> None:
    data = load_json("sent_emails.json")
    data["emails"].append(email.model_dump())
    save_json("sent_emails.json", data)
