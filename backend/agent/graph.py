from langgraph.graph import StateGraph, END

from backend.models.state import AgentState
from backend.models.schemas import EmailInput, TraceStep
from backend.agent.nodes.input_guardrail import input_guardrail_node
from backend.agent.nodes.main_agent import main_agent_node
from backend.agent.nodes.output_guardrail import output_guardrail_node
from backend.agent.nodes.send_email import send_email_node
from backend.agent.nodes.human_queue import human_queue_node
from backend.agent.nodes.default_response import default_response_node


def route_after_input_guardrail(state: AgentState) -> str:
    """Routes based on input guardrail classification."""
    route = state.get("route", "human_queue")
    return route


def route_after_main_agent(state: AgentState) -> str:
    """Routes based on main agent result."""
    route = state.get("route", "human_queue")
    return route


def route_after_output_guardrail(state: AgentState) -> str:
    """Routes based on output guardrail validation."""
    route = state.get("route", "human_queue")
    return route


def build_graph() -> StateGraph:
    """Builds and compiles the customer support agent graph."""

    # Create the graph with our state
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("input_guardrail", input_guardrail_node)
    workflow.add_node("main_agent", main_agent_node)
    workflow.add_node("output_guardrail", output_guardrail_node)
    workflow.add_node("send_email", send_email_node)
    workflow.add_node("human_queue", human_queue_node)
    workflow.add_node("default_response", default_response_node)

    # Set entry point
    workflow.set_entry_point("input_guardrail")

    # Add conditional edges after input guardrail
    workflow.add_conditional_edges(
        "input_guardrail",
        route_after_input_guardrail,
        {
            "main_agent": "main_agent",
            "human_queue": "human_queue",
            "default_response": "default_response"
        }
    )

    # Add conditional edges after main agent
    workflow.add_conditional_edges(
        "main_agent",
        route_after_main_agent,
        {
            "output_guardrail": "output_guardrail",
            "human_queue": "human_queue",
            "default_response": "default_response"
        }
    )

    # Add conditional edges after output guardrail
    workflow.add_conditional_edges(
        "output_guardrail",
        route_after_output_guardrail,
        {
            "send_email": "send_email",
            "human_queue": "human_queue"
        }
    )

    # Terminal edges - all end nodes go to END
    workflow.add_edge("send_email", END)
    workflow.add_edge("human_queue", END)
    workflow.add_edge("default_response", END)

    # Compile and return
    return workflow.compile()


# Pre-compile the graph for use
agent_graph = build_graph()


def get_graph_mermaid() -> str:
    """Returns a Mermaid diagram of the graph."""
    mermaid = """graph TD
    START([Start]) --> input_guardrail[Input Guardrail]

    input_guardrail -->|order_status| main_agent[Main Agent]
    input_guardrail -->|other| human_queue[Human Queue]
    input_guardrail -->|prompt_injection| default_response[Default Response]
    input_guardrail -->|out_of_scope| default_response

    main_agent -->|user_found| output_guardrail[Output Guardrail]
    main_agent -->|user_not_found| default_response
    main_agent -->|error| human_queue

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
    class main_agent agent
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
        "validated_user_id": None
    }

    # Run the graph
    final_state = agent_graph.invoke(initial_state)

    return final_state
