import pytest
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services import database
from backend.agent.tools.user_tools import get_user_by_email, validate_email_matches_sender
from backend.agent.tools.order_tools import get_orders_for_user, get_order_by_id, validate_user_id_matches
from backend.agent.tools.email_tools import validate_recipient_matches_sender


class TestUserTools:
    def test_get_user_by_email_found(self):
        result = get_user_by_email.invoke({"email": "john.doe@email.com"})
        assert result["found"] is True
        assert result["user_id"] == "usr_001"
        assert result["name"] == "John Doe"

    def test_get_user_by_email_not_found(self):
        result = get_user_by_email.invoke({"email": "nonexistent@email.com"})
        assert result["found"] is False
        assert "error" in result

    def test_get_user_by_email_case_insensitive(self):
        result = get_user_by_email.invoke({"email": "JOHN.DOE@EMAIL.COM"})
        assert result["found"] is True

    def test_validate_email_matches_sender(self):
        assert validate_email_matches_sender("john@email.com", "john@email.com") is True
        assert validate_email_matches_sender("john@email.com", "JOHN@EMAIL.COM") is True
        assert validate_email_matches_sender("john@email.com", "jane@email.com") is False


class TestOrderTools:
    def test_get_orders_for_user_found(self):
        result = get_orders_for_user.invoke({"user_id": "usr_001", "days": 30})
        assert result["found"] is True
        assert result["count"] > 0
        assert len(result["orders"]) > 0

    def test_get_orders_for_user_not_found(self):
        result = get_orders_for_user.invoke({"user_id": "nonexistent", "days": 14})
        assert result["found"] is False
        assert result["count"] == 0

    def test_get_order_by_id_found(self):
        result = get_order_by_id.invoke({"order_id": "ORD-2024-001234"})
        assert result["found"] is True
        assert result["product_name"] == "Wireless Bluetooth Headphones"

    def test_get_order_by_id_not_found(self):
        result = get_order_by_id.invoke({"order_id": "ORD-NONEXISTENT"})
        assert result["found"] is False

    def test_validate_user_id_matches(self):
        assert validate_user_id_matches("usr_001", "usr_001") is True
        assert validate_user_id_matches("usr_001", "usr_002") is False


class TestEmailTools:
    def test_validate_recipient_matches_sender(self):
        assert validate_recipient_matches_sender("john@email.com", "john@email.com") is True
        assert validate_recipient_matches_sender("john@email.com", "jane@email.com") is False


class TestDatabase:
    def test_get_all_users(self):
        users = database.get_all_users()
        assert len(users) >= 5
        assert any(u.email == "john.doe@email.com" for u in users)

    def test_get_all_orders(self):
        orders = database.get_all_orders()
        assert len(orders) >= 9

    def test_get_user_by_email(self):
        user = database.get_user_by_email("jane.smith@email.com")
        assert user is not None
        assert user.name == "Jane Smith"
        assert user.user_id == "usr_002"
