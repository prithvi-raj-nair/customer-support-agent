from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    ProcessEmailRequest,
    ProcessEmailResponse,
    EmailInput,
    EmailResponse,
    TraceStep
)
from backend.agent.graph import run_agent
from backend.services import database

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/process", response_model=ProcessEmailResponse)
async def process_email(request: ProcessEmailRequest):
    """
    Process an incoming customer email through the agent pipeline.
    Returns the response and execution trace.
    """
    try:
        # Create EmailInput from request
        email_input = EmailInput(
            sender_email=request.sender_email,
            subject=request.subject,
            body=request.body
        )

        # Run the agent
        final_state = run_agent(email_input)

        # Determine routed_to based on the execution path
        trace = final_state.get("trace", [])
        if trace:
            last_node = trace[-1].node if isinstance(trace[-1], TraceStep) else trace[-1]["node"]
            if last_node == "send_email":
                routed_to = "automated_response"
            elif last_node == "human_queue":
                routed_to = "human_queue"
            elif last_node == "default_response":
                routed_to = "default_response"
            else:
                routed_to = "unknown"
        else:
            routed_to = "unknown"

        # Get the response email if one was sent
        response_email = None
        final_response = final_state.get("final_response")
        if final_response:
            response_email = EmailResponse(
                to_email=request.sender_email,
                subject=f"Re: {request.subject}",
                body=final_response,
                timestamp=trace[-1].timestamp if trace else ""
            )

        # Convert trace to list of dicts if needed
        trace_list = []
        for step in trace:
            if isinstance(step, TraceStep):
                trace_list.append(step)
            elif isinstance(step, dict):
                trace_list.append(TraceStep(**step))

        return ProcessEmailResponse(
            success=True,
            response_email=response_email,
            routed_to=routed_to,
            escalation_reason=final_state.get("escalation_reason"),
            trace=trace_list,
            error=final_state.get("error")
        )

    except Exception as e:
        return ProcessEmailResponse(
            success=False,
            response_email=None,
            routed_to="error",
            escalation_reason=None,
            trace=[],
            error=str(e)
        )


@router.get("/sent")
async def get_sent_emails():
    """Get all sent emails."""
    emails = database.get_sent_emails()
    return {"emails": [e.model_dump() for e in emails]}
