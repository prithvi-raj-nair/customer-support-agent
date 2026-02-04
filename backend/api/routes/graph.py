from fastapi import APIRouter
from backend.agent.graph import get_graph_mermaid

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/definition")
async def get_graph_definition():
    """Get the Mermaid diagram definition for the agent graph."""
    return {
        "mermaid": get_graph_mermaid(),
        "description": "Shamazon Customer Support Agent Graph"
    }
