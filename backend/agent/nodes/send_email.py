from datetime import datetime

from backend.models.state import AgentState
from backend.models.schemas import TraceStep, EmailResponse
from backend.services import database


def send_email_node(state: AgentState) -> dict:
    """
    Sends the validated email response to the customer.
    """
    start_time = datetime.utcnow()

    email_input = state["email_input"]
    final_response = state.get("final_response", "")

    try:
        # Create and save the email response
        email_response = EmailResponse(
            to_email=email_input.sender_email,
            subject=f"Re: {email_input.subject}",
            body=final_response,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        database.save_sent_email(email_response)

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="send_email",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Sending response to {email_input.sender_email}",
            output_summary=f"Email sent successfully",
            duration_ms=duration
        )

        return {
            "trace": [trace_step]
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="send_email",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Sending response to {email_input.sender_email}",
            output_summary=f"Error: {str(e)}",
            duration_ms=duration
        )

        return {
            "error": str(e),
            "trace": [trace_step]
        }
