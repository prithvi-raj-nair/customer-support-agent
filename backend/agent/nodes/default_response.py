from datetime import datetime

from backend.models.state import AgentState
from backend.models.schemas import TraceStep, EmailResponse
from backend.services import database
from backend.agent.prompts.guardrail_prompts import DEFAULT_RESPONSES


def default_response_node(state: AgentState) -> dict:
    """
    Sends a default response based on the classification or error type.
    """
    start_time = datetime.utcnow()

    email_input = state["email_input"]
    input_guardrail_result = state.get("input_guardrail_result")
    escalation_reason = state.get("escalation_reason")

    # Determine which default response to use
    if escalation_reason == "user_not_found":
        response_key = "user_not_found"
    elif input_guardrail_result:
        query_type = input_guardrail_result.query_type
        if query_type == "prompt_injection":
            response_key = "prompt_injection"
        elif query_type == "out_of_scope":
            response_key = "out_of_scope"
        else:
            response_key = "technical_error"
    else:
        response_key = "technical_error"

    response_body = DEFAULT_RESPONSES.get(response_key, DEFAULT_RESPONSES["technical_error"])

    try:
        # Send the default response
        email_response = EmailResponse(
            to_email=email_input.sender_email,
            subject=f"Re: {email_input.subject}",
            body=response_body,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        database.save_sent_email(email_response)

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="default_response",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Sending default response ({response_key}) to {email_input.sender_email}",
            output_summary=f"Default response sent",
            duration_ms=duration
        )

        return {
            "final_response": response_body,
            "trace": [trace_step]
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="default_response",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Sending default response to {email_input.sender_email}",
            output_summary=f"Error: {str(e)}",
            duration_ms=duration
        )

        return {
            "error": str(e),
            "trace": [trace_step]
        }
