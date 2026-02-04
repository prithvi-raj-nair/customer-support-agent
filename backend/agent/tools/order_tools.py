from langchain_core.tools import tool
from backend.services import database
from typing import Optional


class OrderToolValidationError(Exception):
    pass


@tool
def get_orders_for_user(user_id: str, days: int = 14) -> dict:
    """
    Get all orders for a user within the specified number of days.
    Returns a list of orders with their details and status.

    Args:
        user_id: The user ID to fetch orders for
        days: Number of days to look back (default 14)
    """
    orders = database.get_orders_for_user(user_id, days)

    if orders:
        return {
            "found": True,
            "count": len(orders),
            "orders": [
                {
                    "order_id": o.order_id,
                    "user_id": o.user_id,
                    "product_name": o.product_name,
                    "status": o.status,
                    "tracking_number": o.tracking_number,
                    "estimated_delivery": o.estimated_delivery,
                    "order_date": o.order_date,
                    "total_amount": o.total_amount
                }
                for o in orders
            ]
        }
    else:
        return {
            "found": False,
            "count": 0,
            "orders": [],
            "message": f"No orders found for user {user_id} in the last {days} days"
        }


@tool
def get_order_by_id(order_id: str) -> dict:
    """
    Get details for a specific order by its order ID.

    Args:
        order_id: The order ID to look up
    """
    order = database.get_order_by_id(order_id)

    if order:
        return {
            "found": True,
            "order_id": order.order_id,
            "user_id": order.user_id,
            "product_name": order.product_name,
            "status": order.status,
            "tracking_number": order.tracking_number,
            "estimated_delivery": order.estimated_delivery,
            "order_date": order.order_date,
            "total_amount": order.total_amount
        }
    else:
        return {
            "found": False,
            "error": f"No order found with ID: {order_id}"
        }


def validate_user_id_matches(user_id: str, validated_user_id: str) -> bool:
    """Validate that the user_id being queried matches the validated user."""
    return user_id == validated_user_id
