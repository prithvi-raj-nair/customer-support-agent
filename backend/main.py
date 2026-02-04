from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.api.routes import email, data, queue, graph

# Create FastAPI app
app = FastAPI(
    title="Shamazon Customer Support Agent",
    description="AI-powered customer support agent for order status inquiries",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(email.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(queue.router, prefix="/api")
app.include_router(graph.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Shamazon Customer Support Agent API",
        "docs": "/docs",
        "endpoints": {
            "process_email": "POST /api/email/process",
            "get_users": "GET /api/data/users",
            "get_orders": "GET /api/data/orders",
            "get_queue": "GET /api/queue",
            "get_graph": "GET /api/graph/definition"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Mount static files for frontend (if running with frontend)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
