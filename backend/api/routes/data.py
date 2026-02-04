from fastapi import APIRouter, Query
from typing import Optional
from backend.services import database

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/users")
async def get_users():
    """Get all users in the system."""
    users = database.get_all_users()
    return {"users": [u.model_dump() for u in users]}


@router.get("/orders")
async def get_orders(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    days: int = Query(14, description="Number of days to look back")
):
    """Get orders, optionally filtered by user and date range."""
    if user_id:
        orders = database.get_orders_for_user(user_id, days)
    else:
        orders = database.get_all_orders()

    return {"orders": [o.model_dump() for o in orders]}


@router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get a specific order by ID."""
    order = database.get_order_by_id(order_id)
    if order:
        return order.model_dump()
    return {"error": "Order not found"}
