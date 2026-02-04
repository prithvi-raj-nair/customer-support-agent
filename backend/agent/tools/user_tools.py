from langchain_core.tools import tool
from backend.services import database
from backend.models.schemas import User
from typing import Optional


class UserToolValidationError(Exception):
    pass


@tool
def get_user_by_email(email: str) -> dict:
    """
    Look up a user by their email address.
    Returns user details if found, or an error message if not found.

    Args:
        email: The email address to look up
    """
    user = database.get_user_by_email(email)

    if user:
        return {
            "found": True,
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name
        }
    else:
        return {
            "found": False,
            "error": f"No user found with email: {email}"
        }


def validate_email_matches_sender(email: str, sender_email: str) -> bool:
    """Validate that the email being looked up matches the original sender."""
    return email.lower() == sender_email.lower()
