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
from backend.services import database


def main_agent_node(state: AgentState) -> dict:
    """
    Main agent that handles order status queries.
    Uses tools to fetch user and order data, then composes a response.
    """
    start_time = datetime.utcnow()

    email_input = state["email_input"]
    validated_sender = state.get("validated_sender_email", email_input.sender_email)

    # Build the conversation context
    email_content = f"""
Customer Email:
From: {email_input.sender_email}
Subject: {email_input.subject}

{email_input.body}
"""

    # Initialize the LLM with tools
    tools = [get_user_by_email, get_orders_for_user, get_order_by_id]
    llm = ChatAnthropic(
        model=MAIN_MODEL,
        api_key=ANTHROPIC_API_KEY,
        temperature=0.3
    )
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = MAIN_AGENT_SYSTEM_PROMPT + TOOL_CALLING_INSTRUCTIONS

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please help this customer with their order status inquiry:\n\n{email_content}")
    ]

    user = None
    orders = []
    matched_order = None
    tool_calls_made = []

    try:
        # Agent loop - allow up to 5 tool calls
        max_iterations = 5
        for iteration in range(max_iterations):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # Check if there are tool calls
            if not response.tool_calls:
                # No more tool calls, we have the final response
                break

            # Process tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                tool_calls_made.append({"name": tool_name, "args": tool_args})

                # Execute the tool with validation
                if tool_name == "get_user_by_email":
                    # Validate email matches sender
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
                                name=tool_result["name"]
                            )

                elif tool_name == "get_orders_for_user":
                    # Validate user_id matches the looked-up user
                    user_id_arg = tool_args.get("user_id", "")
                    if user and user_id_arg != user.user_id:
                        tool_result = {
                            "error": "Security validation failed: Can only fetch orders for the verified user"
                        }
                    elif not user:
                        tool_result = {
                            "error": "Must look up user first before fetching orders"
                        }
                    else:
                        tool_result = get_orders_for_user.invoke(tool_args)
                        if tool_result.get("found"):
                            orders = [Order(**o) for o in tool_result["orders"]]

                elif tool_name == "get_order_by_id":
                    tool_result = get_order_by_id.invoke(tool_args)
                    if tool_result.get("found") and user:
                        # Verify order belongs to user
                        if tool_result["user_id"] != user.user_id:
                            tool_result = {
                                "error": "Security validation failed: Order does not belong to this user"
                            }
                        else:
                            matched_order = Order(**{k: v for k, v in tool_result.items() if k != "found"})

                else:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}

                # Add tool result to messages
                messages.append(ToolMessage(
                    content=json.dumps(tool_result),
                    tool_call_id=tool_id
                ))

        # Extract the final response
        final_message = messages[-1]
        if isinstance(final_message, AIMessage):
            draft_response = final_message.content
        else:
            draft_response = "I apologize, but I was unable to process your request. Please try again."

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Determine if we should route to output validation or handle missing user
        if not user:
            route = "default_response"
            escalation_reason = "user_not_found"
        else:
            route = "output_guardrail"
            escalation_reason = None

        trace_step = TraceStep(
            node="main_agent",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Order status query from {email_input.sender_email}",
            output_summary=f"User: {user.name if user else 'Not found'}, Orders: {len(orders)}, Tools used: {len(tool_calls_made)}",
            duration_ms=duration
        )

        return {
            "user": user,
            "orders": orders,
            "matched_order": matched_order,
            "draft_response": draft_response,
            "validated_user_id": user.user_id if user else None,
            "route": route,
            "escalation_reason": escalation_reason,
            "trace": [trace_step]
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        trace_step = TraceStep(
            node="main_agent",
            timestamp=start_time.isoformat() + "Z",
            input_summary=f"Order status query from {email_input.sender_email}",
            output_summary=f"Error: {str(e)}",
            duration_ms=duration
        )

        return {
            "error": str(e),
            "route": "human_queue",
            "escalation_reason": f"Main agent error: {str(e)}",
            "trace": [trace_step]
        }
