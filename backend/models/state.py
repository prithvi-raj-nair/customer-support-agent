from typing import TypedDict, Optional, Annotated, Literal
import operator
from backend.models.schemas import EmailInput, User, Order, GuardrailResult, TraceStep


class AgentState(TypedDict):
    # Input
    email_input: EmailInput

    # User and orders data
    user: Optional[User]
    orders: list[Order]
    matched_order: Optional[Order]

    # Guardrail results
    input_guardrail_result: Optional[GuardrailResult]
    output_guardrail_result: Optional[GuardrailResult]

    # Response drafts
    draft_response: Optional[str]
    final_response: Optional[str]

    # Routing
    route: Literal["main_agent", "human_queue", "default_response", "send_email"]
    escalation_reason: Optional[str]

    # Execution trace (append-only)
    trace: Annotated[list[TraceStep], operator.add]

    # Error tracking
    error: Optional[str]

    # Validated sender email for tool validation
    validated_sender_email: Optional[str]
    validated_user_id: Optional[str]
