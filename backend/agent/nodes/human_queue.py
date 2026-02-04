from datetime import datetime

from backend.models.state import AgentState
from backend.models.schemas import TraceStep, EmailResponse
from backend.services import database
from backend.agent.prompts.guardrail_prompts import DEFAULT_RESPONSES


def human_queue_node(state: AgentState) -> dict:
    """
    Adds the case to the human queue and sends an acknowledgment email.
    """
    start_time = datetime.utcnow()

    email_input = state["email_input"]
    escalation_reason = state.get("escalation_reason") or "Requires human review"

    try:
        # Add to human queue
        queue_item = database.add_to_human_queue(email_input, escalation_reason)

        # Send acknowledgment email
        acknowledgment = DEFAULT_RESPONSES["escalated"]

        email_response = EmailResponse(
            to_email=email_input.sender_email,
            subject=f"Re: {email_input.subject}",
            body=acknowledgment,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        database.save_sent_email(email_response)

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="human_queue",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Escalating case from {email_input.sender_email}",
            output_summary=f"Added to queue (ID: {queue_item.id[:8]}...), sent acknowledgment",
            duration_ms=duration
        )

        return {
            "final_response": acknowledgment,
            "trace": [trace_step]
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="human_queue",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Escalating case from {email_input.sender_email}",
            output_summary=f"Error: {str(e)}",
            duration_ms=duration
        )

        return {
            "error": str(e),
            "trace": [trace_step]
        }
