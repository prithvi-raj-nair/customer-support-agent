from langgraph.graph import StateGraph, END

from backend.models.state import AgentState
from backend.models.schemas import EmailInput, TraceStep
from backend.agent.nodes.input_guardrail import input_guardrail_node
from backend.agent.nodes.main_agent import (
    main_agent_llm_node,
    main_agent_tools_node,
    main_agent_router_node,
    should_continue_tools,
)
from backend.agent.nodes.output_guardrail import output_guardrail_node
from backend.agent.nodes.send_email import send_email_node
from backend.agent.nodes.human_queue import human_queue_node
from backend.agent.nodes.default_response import default_response_node


def route_after_input_guardrail(state: AgentState) -> str:
    """Routes based on input guardrail classification."""
    route = state.get("route", "human_queue")
    # The input guardrail sets route="main_agent"; map to the LLM entry node
    if route == "main_agent":
        return "main_agent_llm"
    return route


def route_after_main_agent(state: AgentState) -> str:
    """Routes based on main agent router result."""
    route = state.get("route", "human_queue")
    return route


def route_after_output_guardrail(state: AgentState) -> str:
    """Routes based on output guardrail validation."""
    route = state.get("route", "human_queue")
    return route


def build_graph() -> StateGraph:
    """Builds and compiles the customer support agent graph."""

    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("main_agent_llm", main_agent_llm_node)
    workflow.add_node("main_agent_tools", main_agent_tools_node)
    workflow.add_node("main_agent_router", main_agent_router_node)
    workflow.add_node("output_guardrail", output_guardrail_node)
    workflow.add_node("send_email", send_email_node)
    workflow.add_node("human_queue", human_queue_node)
    workflow.add_node("default_response", default_response_node)

    # Set entry point
    workflow.set_entry_point("input_guardrail")

    # After input guardrail: route to main_agent_llm, human_queue, or default_response
    workflow.add_conditional_edges(
        "input_guardrail",
        route_after_input_guardrail,
        {
            "main_agent_llm": "main_agent_llm",
            "human_queue": "human_queue",
            "default_response": "default_response",
        },
    )

    # After LLM: either call tools (loop) or proceed to router
    workflow.add_conditional_edges(
        "main_agent_llm",
        should_continue_tools,
        {
            "main_agent_tools": "main_agent_tools",
            "main_agent_router": "main_agent_router",
        },
    )

    # After tools: loop back to LLM
    workflow.add_edge("main_agent_tools", "main_agent_llm")

    # After router: route to output_guardrail, human_queue, or default_response
    workflow.add_conditional_edges(
        "main_agent_router",
        route_after_main_agent,
        {
            "output_guardrail": "output_guardrail",
            "human_queue": "human_queue",
            "default_response": "default_response",
        },
    )

    # After output guardrail
    workflow.add_conditional_edges(
        "output_guardrail",
        route_after_output_guardrail,
        {
            "send_email": "send_email",
            "human_queue": "human_queue",
        },
    )

    # Terminal edges
    workflow.add_edge("send_email", END)
    workflow.add_edge("human_queue", END)
    workflow.add_edge("default_response", END)

    return workflow.compile()


# Pre-compile the graph for use
agent_graph = build_graph()


def get_graph_mermaid() -> str:
    """Returns a Mermaid diagram of the graph."""
    mermaid = """graph TD
    START([Start]) --> input_guardrail[Input Guardrail]

    input_guardrail -->|order_status| main_agent_llm[Main Agent LLM]
    input_guardrail -->|other| human_queue[Human Queue]
    input_guardrail -->|prompt_injection| default_response[Default Response]
    input_guardrail -->|out_of_scope| default_response

    main_agent_llm -->|tool_calls| main_agent_tools[Main Agent Tools]
    main_agent_llm -->|done| main_agent_router[Main Agent Router]
    main_agent_tools --> main_agent_llm

    main_agent_router -->|user_found| output_guardrail[Output Guardrail]
    main_agent_router -->|user_not_found| default_response
    main_agent_router -->|error| human_queue

    output_guardrail -->|passed| send_email[Send Email]
    output_guardrail -->|failed| human_queue

    send_email --> END([End])
    human_queue --> END
    default_response --> END

    classDef guardrail fill:#ffd700,stroke:#333,stroke-width:2px
    classDef agent fill:#90EE90,stroke:#333,stroke-width:2px
    classDef action fill:#87CEEB,stroke:#333,stroke-width:2px
    classDef terminal fill:#DDA0DD,stroke:#333,stroke-width:2px

    class input_guardrail,output_guardrail guardrail
    class main_agent_llm,main_agent_tools,main_agent_router agent
    class send_email,human_queue,default_response action
    class START,END terminal
"""
    return mermaid


def run_agent(email_input: EmailInput) -> AgentState:
    """
    Runs the agent graph with the given email input.
    Returns the final state after execution.
    """
    initial_state: AgentState = {
        "email_input": email_input,
        "user": None,
        "orders": [],
        "matched_order": None,
        "input_guardrail_result": None,
        "output_guardrail_result": None,
        "draft_response": None,
        "final_response": None,
        "route": "input_guardrail",
        "escalation_reason": None,
        "trace": [],
        "error": None,
        "validated_sender_email": None,
        "validated_user_id": None,
        "messages": [],
    }

    # Run the graph
    final_state = agent_graph.invoke(initial_state)

    return final_state
