# Shamazon Customer Support Agent - Implementation Plan

## Overview

Build an AI-powered customer support agent for "Shamazon" that handles order status email queries using LangGraph, Anthropic Claude, and a simple web UI with visualizations.

## Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Agent Framework | LangGraph | Stateful workflows, conditional routing, human-in-the-loop |
| Main LLM | Claude Sonnet | Complex reasoning, tool calling |
| Guardrail LLM | Claude Haiku | Fast, cheap validation |
| Backend | FastAPI | Modern Python API, async support |
| Frontend | HTML/JS + Mermaid.js | Simple, no build step, native graph rendering |
| Database | JSON files | Easy to inspect, modify, and demo |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         WEB UI                                  │
│  [Email Simulator] [Agent Graph] [Data Viewer] [Human Queue]   │
└────────────────────────────────────────────────────────────────┘
                              │ HTTP
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LANGGRAPH STATE GRAPH                        │  │
│  │                                                           │  │
│  │  START → [input_guardrail] → {router}                    │  │
│  │                                │                          │  │
│  │            ┌───────────────────┼───────────────────┐     │  │
│  │            ▼                   ▼                   ▼     │  │
│  │     [main_agent]        [human_queue]      [default_resp]│  │
│  │            │                   │                   │     │  │
│  │            ▼                   │                   │     │  │
│  │   [output_guardrail]          │                   │     │  │
│  │            │                   │                   │     │  │
│  │      ┌─────┴─────┐            │                   │     │  │
│  │      ▼           ▼            │                   │     │  │
│  │  [send_email] [human_queue]   │                   │     │  │
│  │      │           │            │                   │     │  │
│  │      └───────────┴────────────┴───────────────────┘     │  │
│  │                         END                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                    JSON DATA FILES                              │
│    users.json | orders.json | human_queue.json | sent_emails   │
└────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
customer-support-agent-basic/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry
│   ├── config.py                  # Settings (API keys)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py             # Pydantic API models
│   │   └── state.py               # LangGraph AgentState
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py               # LangGraph definition
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── input_guardrail.py
│   │   │   ├── main_agent.py
│   │   │   ├── output_guardrail.py
│   │   │   ├── send_email.py
│   │   │   ├── human_queue.py
│   │   │   └── default_response.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── user_tools.py      # get_user_by_email
│   │   │   ├── order_tools.py     # get_orders_for_user
│   │   │   └── email_tools.py     # send_email mock
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── system_prompt.py
│   │       └── guardrail_prompts.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── database.py            # JSON file operations
│   └── api/
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           ├── email.py           # POST /api/email/process
│           ├── data.py            # GET /api/users, /api/orders
│           ├── queue.py           # GET /api/queue
│           └── graph.py           # GET /api/graph/definition
├── data/
│   ├── users.json
│   ├── orders.json
│   ├── human_queue.json
│   └── sent_emails.json
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       └── components/
│           ├── emailForm.js
│           ├── responseViewer.js
│           ├── graphViewer.js
│           ├── traceViewer.js
│           ├── dataViewer.js
│           └── queueViewer.js
├── tests/
│   ├── test_tools.py
│   ├── test_nodes.py
│   └── test_graph.py
├── requirements.txt
└── README.md
```

---

## Implementation Phases

### Phase 1: Foundation
1. Create directory structure
2. Set up `requirements.txt`:
   ```
   fastapi
   uvicorn
   langgraph
   langchain-anthropic
   langchain-core
   pydantic
   python-dotenv
   ```
3. Create `config.py` with environment settings
4. Create JSON data files with sample data
5. Implement `database.py` (load/save functions)
6. Set up basic FastAPI app with CORS

### Phase 2: Agent Core
7. Define `AgentState` TypedDict in `state.py`
8. Implement tools with validation:
   - `get_user_by_email` (validates email matches sender)
   - `get_orders_for_user` (validates user_id consistency)
   - `send_email` mock
9. Create prompt templates for guardrails and main agent

### Phase 3: Graph Nodes
10. Implement `input_guardrail` node (Haiku - classifies query type)
11. Implement `main_agent` node (Sonnet - tool calling agent)
12. Implement `output_guardrail` node (Haiku - validates response)
13. Implement `send_email_node`, `human_queue_node`, `default_response_node`

### Phase 4: Graph Assembly
14. Build LangGraph StateGraph in `graph.py`:
    - Add all nodes
    - Define conditional routing edges
    - Compile graph
15. Add graph visualization export (Mermaid)

### Phase 5: API Layer
16. Implement endpoints:
    - `POST /api/email/process` - process email, return response + trace
    - `GET /api/users` - list users
    - `GET /api/orders` - list orders (filterable)
    - `GET /api/queue` - list human queue
    - `GET /api/graph/definition` - Mermaid diagram

### Phase 6: Frontend
17. Create HTML structure with tabs
18. Implement components:
    - Email form (with test scenario presets)
    - Response viewer
    - Graph viewer (Mermaid rendering)
    - Trace viewer (execution steps)
    - Data viewer (tables)
    - Queue viewer

### Phase 7: Testing & Polish
19. Write tests for tools, nodes, and full graph
20. End-to-end testing with various scenarios
21. Documentation

---

## Key Implementation Details

### AgentState Schema

```python
class AgentState(TypedDict):
    email_input: EmailInput           # sender, subject, body
    user: Optional[User]              # from get_user_by_email
    orders: list[Order]               # from get_orders_for_user
    matched_order: Optional[Order]    # order matching query
    input_guardrail_result: GuardrailResult
    output_guardrail_result: GuardrailResult
    draft_response: Optional[str]
    final_response: Optional[str]
    route: Literal["main_agent", "human_queue", "default_response"]
    escalation_reason: Optional[str]
    trace: Annotated[list[TraceStep], operator.add]  # append-only
    error: Optional[str]
```

### Routing Logic

| Input Guardrail Result | Route To |
|------------------------|----------|
| query_type="order_status", passed=True | main_agent |
| query_type="other" | human_queue |
| query_type="prompt_injection" | default_response |
| query_type="out_of_scope" | default_response |
| Any error | human_queue |

### Tool Validations (Code-Based)

- `get_user_by_email`: email param must match sender_email
- `get_orders_for_user`: user_id must match validated user
- `send_email`: recipient must match original sender

### Default Responses

```python
DEFAULT_RESPONSES = {
    "prompt_injection": "I can only help with Shamazon order-related inquiries.",
    "out_of_scope": "I specialize in order status inquiries. For other questions, visit our help center.",
    "user_not_found": "We couldn't find an account with this email address.",
    "technical_error": "We're experiencing technical difficulties. A representative will follow up.",
    "escalated": "Your request has been forwarded to our support team."
}
```

---

## Sample Data

### users.json
```json
{
  "users": [
    {"user_id": "usr_001", "email": "john.doe@email.com", "name": "John Doe"},
    {"user_id": "usr_002", "email": "jane.smith@email.com", "name": "Jane Smith"},
    {"user_id": "usr_003", "email": "bob.wilson@email.com", "name": "Bob Wilson"}
  ]
}
```

### orders.json (sample)
```json
{
  "orders": [
    {
      "order_id": "ORD-2024-001234",
      "user_id": "usr_001",
      "product_name": "Wireless Bluetooth Headphones",
      "status": "shipped",
      "tracking_number": "1Z999AA10123456784",
      "estimated_delivery": "2024-02-10",
      "order_date": "2024-02-01T16:30:00Z",
      "total_amount": 79.99
    }
  ]
}
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/email/process` | Process email, returns response + trace |
| GET | `/api/users` | List all users |
| GET | `/api/orders` | List orders (query: user_id, days) |
| GET | `/api/queue` | List human queue items |
| POST | `/api/queue/{id}/resolve` | Mark queue item resolved |
| GET | `/api/graph/definition` | Get Mermaid diagram |

---

## Verification Steps

1. **Unit tests**: `pytest tests/` - test tools, nodes
2. **Start backend**: `uvicorn backend.main:app --reload`
3. **Open frontend**: Open `frontend/index.html` in browser
4. **Test scenarios**:
   - Valid user, order status query → should respond with order details
   - Invalid user email → should say user not found
   - Non-order query (e.g., "refund request") → should route to human queue
   - Prompt injection attempt → should return default response
5. **Check visualizations**: Graph should render, trace should show execution path
6. **Check data viewers**: Users/orders tables should populate

---

## Dependencies

```txt
fastapi>=0.109.0
uvicorn>=0.27.0
langgraph>=0.0.40
langchain-anthropic>=0.1.0
langchain-core>=0.1.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pytest>=7.0.0
httpx>=0.26.0
```
