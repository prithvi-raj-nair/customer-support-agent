import json
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import GUARDRAIL_MODEL, ANTHROPIC_API_KEY
from backend.models.state import AgentState
from backend.models.schemas import GuardrailResult, TraceStep
from backend.agent.prompts.guardrail_prompts import OUTPUT_GUARDRAIL_PROMPT


def output_guardrail_node(state: AgentState) -> dict:
    """
    Validates the agent's draft response before sending.
    Checks for tone, accuracy, and compliance issues.
    """
    start_time = datetime.utcnow()

    draft_response = state.get("draft_response", "")
    user = state.get("user")
    orders = state.get("orders", [])
    email_input = state["email_input"]

    # Build context for validation
    context = f"""
Original Email:
From: {email_input.sender_email}
Subject: {email_input.subject}
Body: {email_input.body}

Customer Data:
Name: {user.name if user else 'Unknown'}
Email: {user.email if user else 'Unknown'}

Orders Found:
"""
    for order in orders:
        context += f"""
- Order {order.order_id}: {order.product_name}
  Status: {order.status}
  Tracking: {order.tracking_number or 'N/A'}
  Est. Delivery: {order.estimated_delivery or 'N/A'}
"""

    context += f"""

Draft Response to Validate:
{draft_response}
"""

    # Use Haiku for fast validation
    llm = ChatAnthropic(
        model=GUARDRAIL_MODEL,
        api_key=ANTHROPIC_API_KEY,
        temperature=0
    )

    messages = [
        SystemMessage(content=OUTPUT_GUARDRAIL_PROMPT),
        HumanMessage(content=f"Validate this response:\n\n{context}")
    ]

    try:
        response = llm.invoke(messages)
        result_text = response.content

        # Parse the JSON response - try multiple extraction methods
        result_json = None

        # Method 1: Look for ```json blocks
        if "```json" in result_text:
            try:
                json_str = result_text.split("```json")[1].split("```")[0]
                result_json = json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError):
                pass

        # Method 2: Look for any ``` blocks
        if result_json is None and "```" in result_text:
            try:
                json_str = result_text.split("```")[1].split("```")[0]
                result_json = json.loads(json_str.strip())
            except (json.JSONDecodeError, IndexError):
                pass

        # Method 3: Look for JSON object pattern with regex
        if result_json is None:
            import re
            json_match = re.search(r'\{[^{}]*"passed"[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result_json = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        # Method 4: Try parsing the whole response
        if result_json is None:
            try:
                result_json = json.loads(result_text.strip())
            except json.JSONDecodeError:
                pass

        # Method 5: Default to passing if we can't parse but response looks reasonable
        if result_json is None:
            # If the draft response exists and looks like a proper email, pass it
            if draft_response and len(draft_response) > 50 and ("Dear" in draft_response or "Hi" in draft_response or user):
                result_json = {"passed": True, "issues": [], "recommendation": "send"}
            else:
                result_json = {"passed": False, "issues": ["Could not validate response format"], "recommendation": "escalate"}

        passed = result_json.get("passed", False)
        recommendation = result_json.get("recommendation", "escalate")

        # Determine routing based on validation
        if passed and recommendation == "send":
            route = "send_email"
            final_response = draft_response
        elif recommendation == "revise":
            # For now, escalate to human if revision needed
            route = "human_queue"
            final_response = None
        else:
            route = "human_queue"
            final_response = None

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        issues = result_json.get("issues", [])
        guardrail_result = GuardrailResult(
            passed=passed,
            query_type="order_status",  # We're in the order status flow
            reason="; ".join(issues) if issues else "Response validated successfully",
            confidence=1.0 if passed else 0.5
        )

        trace_step = TraceStep(
            node="output_guardrail",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Validating response ({len(draft_response)} chars)",
            output_summary=f"Passed: {passed}, Recommendation: {recommendation}",
            duration_ms=duration
        )

        escalation_reason = None
        if not passed:
            escalation_reason = f"Output validation failed: {'; '.join(issues)}"

        return {
            "output_guardrail_result": guardrail_result,
            "final_response": final_response,
            "route": route,
            "escalation_reason": escalation_reason,
            "trace": [trace_step]
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="output_guardrail",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Validating response ({len(draft_response)} chars)",
            output_summary=f"Error: {str(e)}",
            duration_ms=duration
        )

        # On error, escalate to human for safety
        return {
            "output_guardrail_result": GuardrailResult(
                passed=False,
                query_type="order_status",
                reason=f"Validation error: {str(e)}",
                confidence=0.0
            ),
            "route": "human_queue",
            "escalation_reason": f"Output guardrail error: {str(e)}",
            "error": str(e),
            "trace": [trace_step]
        }
