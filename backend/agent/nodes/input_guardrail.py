import json
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import GUARDRAIL_MODEL, ANTHROPIC_API_KEY
from backend.models.state import AgentState
from backend.models.schemas import GuardrailResult, TraceStep
from backend.agent.prompts.guardrail_prompts import INPUT_GUARDRAIL_PROMPT


def input_guardrail_node(state: AgentState) -> dict:
    """
    Validates the incoming email using a fast model to classify the query type.
    Routes to appropriate handler based on classification.
    """
    start_time = datetime.utcnow()

    email_input = state["email_input"]

    # Construct the message for classification
    email_content = f"""
From: {email_input.sender_email}
Subject: {email_input.subject}

{email_input.body}
"""

    # Use Haiku for fast, cheap classification
    llm = ChatAnthropic(
        model=GUARDRAIL_MODEL,
        api_key=ANTHROPIC_API_KEY,
        temperature=0
    )

    messages = [
        SystemMessage(content=INPUT_GUARDRAIL_PROMPT),
        HumanMessage(content=f"Classify this email:\n\n{email_content}")
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
            json_match = re.search(r'\{[^{}]*"query_type"[^{}]*\}', result_text, re.DOTALL)
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

        # Method 5: Keyword detection fallback
        if result_json is None:
            result_text_lower = result_text.lower()
            if "prompt_injection" in result_text_lower or "ignore" in result_text_lower and "instruction" in result_text_lower:
                result_json = {"query_type": "prompt_injection", "confidence": 0.8, "reason": "Detected manipulation attempt"}
            elif "out_of_scope" in result_text_lower or "spam" in result_text_lower:
                result_json = {"query_type": "out_of_scope", "confidence": 0.8, "reason": "Not relevant to support"}
            elif "order" in result_text_lower and "status" in result_text_lower:
                result_json = {"query_type": "order_status", "confidence": 0.7, "reason": "Order status inquiry"}
            else:
                result_json = {"query_type": "other", "confidence": 0.5, "reason": "Could not classify"}

        guardrail_result = GuardrailResult(
            passed=result_json["query_type"] == "order_status",
            query_type=result_json["query_type"],
            reason=result_json.get("reason", ""),
            confidence=result_json.get("confidence", 0.0)
        )

        # Determine routing based on classification
        if guardrail_result.query_type == "order_status":
            route = "main_agent"
        elif guardrail_result.query_type == "other":
            route = "human_queue"
        else:  # prompt_injection or out_of_scope
            route = "default_response"

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="input_guardrail",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Email from {email_input.sender_email}: {email_input.subject}",
            output_summary=f"Classified as: {guardrail_result.query_type} (confidence: {guardrail_result.confidence:.2f})",
            duration_ms=duration
        )

        return {
            "input_guardrail_result": guardrail_result,
            "route": route,
            "validated_sender_email": email_input.sender_email,
            "trace": [trace_step]
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="input_guardrail",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Email from {email_input.sender_email}: {email_input.subject}",
            output_summary=f"Error: {str(e)}",
            duration_ms=duration
        )

        # On error, route to human queue for safety
        return {
            "input_guardrail_result": GuardrailResult(
                passed=False,
                query_type="other",
                reason=f"Classification error: {str(e)}",
                confidence=0.0
            ),
            "route": "human_queue",
            "escalation_reason": f"Input guardrail error: {str(e)}",
            "error": str(e),
            "trace": [trace_step]
        }
