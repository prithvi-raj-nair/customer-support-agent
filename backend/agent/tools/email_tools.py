from langchain_core.tools import tool
from backend.services import database
from backend.models.schemas import EmailResponse
from datetime import datetime


class EmailToolValidationError(Exception):
    pass


@tool
def send_email_response(to_email: str, subject: str, body: str) -> dict:
    """
    Send an email response to the customer.
    This is a mock function that saves the email to our sent_emails.json file.

    Args:
        to_email: The recipient email address
        subject: The subject line of the response email
        body: The body content of the response email
    """
    email = EmailResponse(
        to_email=to_email,
        subject=f"Re: {subject}",
        body=body,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

    database.save_sent_email(email)

    return {
        "success": True,
        "message": f"Email sent successfully to {to_email}",
        "email_id": email.timestamp
    }


def validate_recipient_matches_sender(to_email: str, sender_email: str) -> bool:
    """Validate that the email recipient matches the original sender."""
    return to_email.lower() == sender_email.lower()
