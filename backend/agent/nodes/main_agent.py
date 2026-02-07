import json
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from backend.config import MAIN_MODEL, ANTHROPIC_API_KEY
from backend.models.state import AgentState
from backend.models.schemas import TraceStep, User, Order
from backend.agent.prompts.system_prompt import MAIN_AGENT_SYSTEM_PROMPT, TOOL_CALLING_INSTRUCTIONS
from backend.agent.tools.user_tools import get_user_by_email
from backend.agent.tools.order_tools import get_orders_for_user, get_order_by_id

# Max number of LLM -> tool round-trips before forcing a stop
MAX_TOOL_ROUNDS = 5

# LLM with tools bound (initialized once at module level)
_tools = [get_user_by_email, get_orders_for_user, get_order_by_id]
_llm = ChatAnthropic(
    model=MAIN_MODEL,
    api_key=ANTHROPIC_API_KEY,
    temperature=0.3,
)
llm_with_tools = _llm.bind_tools(_tools)


def main_agent_llm_node(state: AgentState) -> dict:
    """
    LLM node: invokes the model with tools bound.
    On the first call, constructs system + human messages from the email input.
    On subsequent calls (after tool results), continues the existing conversation.
    """
    start_time = datetime.utcnow()
    messages = state.get("messages", [])

    try:
        if not messages:
            # First call - build the initial prompt from the email
            email_input = state["email_input"]
            email_content = (
                f"Customer Email:\n"
                f"From: {email_input.sender_email}\n"
                f"Subject: {email_input.subject}\n\n"
                f"{email_input.body}"
            )
            system_prompt = MAIN_AGENT_SYSTEM_PROMPT + TOOL_CALLING_INSTRUCTIONS
            init_messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"Please help this customer with their order status inquiry:\n\n{email_content}"
                ),
            ]
            response = llm_with_tools.invoke(init_messages)
            new_messages = init_messages + [response]
        else:
            # Subsequent calls - continue with full conversation history
            response = llm_with_tools.invoke(messages)
            new_messages = [response]

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        trace_step = TraceStep(
            node="main_agent_llm",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"LLM call (messages: {len(messages) + len(new_messages)})",
            output_summary=f"Tool calls: {len(response.tool_calls) if response.tool_calls else 0}",
            duration_ms=duration,
        )
        return {"messages": new_messages, "trace": [trace_step]}

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        trace_step = TraceStep(
            node="main_agent_llm",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"LLM call (messages: {len(messages)})",
            output_summary=f"Error: {e}",
            duration_ms=duration,
        )
        return {
            "error": str(e),
            "route": "human_queue",
            "escalation_reason": f"Main agent LLM error: {e}",
            "trace": [trace_step],
        }


def should_continue_tools(state: AgentState) -> str:
    """
    Conditional edge after main_agent_llm:
    - If the LLM requested tool calls (and we haven't hit the limit), route to tools.
    - Otherwise, route to the router node for post-processing.
    """
    if state.get("error"):
        return "main_agent_router"

    messages = state.get("messages", [])
    if not messages:
        return "main_agent_router"

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Count completed LLM turns that included tool calls
        tool_rounds = sum(
            1 for m in messages if isinstance(m, AIMessage) and m.tool_calls
        )
        if tool_rounds >= MAX_TOOL_ROUNDS:
            return "main_agent_router"
        return "main_agent_tools"

    return "main_agent_router"


def main_agent_tools_node(state: AgentState) -> dict:
    """
    Tool execution node: processes tool calls from the last AI message.
    Applies the same security validations as the original main_agent_node:
      - get_user_by_email: email must match the validated sender
      - get_orders_for_user: user must be looked up first, user_id must match
      - get_order_by_id: order must belong to the verified user
    Returns ToolMessages and any state updates (user, orders, matched_order).
    """
    start_time = datetime.utcnow()
    messages = state.get("messages", [])
    last_message = messages[-1]

    validated_sender = state.get("validated_sender_email", state["email_input"].sender_email)
    user = state.get("user")
    orders = state.get("orders", [])
    matched_order = state.get("matched_order")

    new_messages = []
    user_update = None
    orders_update = None
    matched_order_update = None
    validated_user_id = state.get("validated_user_id")
    tool_names = []

    try:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            tool_names.append(tool_name)

            if tool_name == "get_user_by_email":
                # Validate: email must match the original sender
                email_arg = tool_args.get("email", "")
                if email_arg.lower() != validated_sender.lower():
                    tool_result = {
                        "error": "Security validation failed: Can only look up the email sender's account"
                    }
                else:
                    tool_result = get_user_by_email.invoke(tool_args)
                    if tool_result.get("found"):
                        user = User(
                            user_id=tool_result["user_id"],
                            email=tool_result["email"],
                            name=tool_result["name"],
                        )
                        user_update = user
                        validated_user_id = user.user_id

            elif tool_name == "get_orders_for_user":
                # Validate: must look up user first, user_id must match
                user_id_arg = tool_args.get("user_id", "")
                if not user:
                    tool_result = {
                        "error": "Must look up user first before fetching orders"
                    }
                elif user_id_arg != user.user_id:
                    tool_result = {
                        "error": "Security validation failed: Can only fetch orders for the verified user"
                    }
                else:
                    tool_result = get_orders_for_user.invoke(tool_args)
                    if tool_result.get("found"):
                        orders = [Order(**o) for o in tool_result["orders"]]
                        orders_update = orders

            elif tool_name == "get_order_by_id":
                tool_result = get_order_by_id.invoke(tool_args)
                if tool_result.get("found") and user:
                    # Validate: order must belong to the verified user
                    if tool_result["user_id"] != user.user_id:
                        tool_result = {
                            "error": "Security validation failed: Order does not belong to this user"
                        }
                    else:
                        matched_order = Order(
                            **{k: v for k, v in tool_result.items() if k != "found"}
                        )
                        matched_order_update = matched_order

            else:
                tool_result = {"error": f"Unknown tool: {tool_name}"}

            new_messages.append(
                ToolMessage(content=json.dumps(tool_result), tool_call_id=tool_id)
            )

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        trace_step = TraceStep(
            node="main_agent_tools",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Tools called: {', '.join(tool_names)}",
            output_summary=f"User: {'found' if user else 'not found'}, Orders: {len(orders)}",
            duration_ms=duration,
        )

        result: dict = {"messages": new_messages, "trace": [trace_step]}
        if user_update is not None:
            result["user"] = user_update
            result["validated_user_id"] = validated_user_id
        if orders_update is not None:
            result["orders"] = orders_update
        if matched_order_update is not None:
            result["matched_order"] = matched_order_update

        return result

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        trace_step = TraceStep(
            node="main_agent_tools",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Tools called: {', '.join(tool_names)}",
            output_summary=f"Error: {e}",
            duration_ms=duration,
        )
        return {
            "messages": new_messages,
            "error": str(e),
            "route": "human_queue",
            "escalation_reason": f"Tool execution error: {e}",
            "trace": [trace_step],
        }


def main_agent_router_node(state: AgentState) -> dict:
    """
    Post-processing node: extracts the draft response from the last AI
    message and determines routing based on whether a user was found.
    """
    start_time = datetime.utcnow()
    messages = state.get("messages", [])
    user = state.get("user")
    email_input = state["email_input"]

    # If there was already an error, just route to human_queue
    if state.get("error"):
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        trace_step = TraceStep(
            node="main_agent_router",
            timestamp=start_time.isoformat() + "Z",
            input_summary="Routing after error",
            output_summary=f"Route: human_queue (error: {state['error']})",
            duration_ms=duration,
        )
        return {
            "route": "human_queue",
            "escalation_reason": state.get("escalation_reason", f"Main agent error: {state['error']}"),
            "trace": [trace_step],
        }

    # Extract draft response from the last AI message
    draft_response = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            draft_response = msg.content
            break

    if not draft_response:
        draft_response = "I apologize, but I was unable to process your request. Please try again."

    # Determine routing
    if not user:
        route = "default_response"
        escalation_reason = "user_not_found"
    else:
        route = "output_guardrail"
        escalation_reason = None

    duration = (datetime.utcnow() - start_time).total_seconds() * 1000
    orders = state.get("orders", [])
    trace_step = TraceStep(
        node="main_agent_router",
        timestamp=start_time.isoformat() + "Z",
        input_summary=f"Order status query from {email_input.sender_email}",
        output_summary=f"User: {user.name if user else 'Not found'}, Orders: {len(orders)}, Route: {route}",
        duration_ms=duration,
    )

    return {
        "draft_response": draft_response,
        "route": route,
        "escalation_reason": escalation_reason,
        "trace": [trace_step],
    }
