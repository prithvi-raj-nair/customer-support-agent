from fastapi import APIRouter, HTTPException
from backend.services import database

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("")
async def get_queue():
    """Get all items in the human queue."""
    items = database.get_human_queue()
    return {"queue": [item.model_dump() for item in items]}


@router.post("/{item_id}/resolve")
async def resolve_queue_item(item_id: str):
    """Mark a queue item as resolved."""
    success = database.resolve_queue_item(item_id)
    if success:
        return {"success": True, "message": f"Item {item_id} marked as resolved"}
    raise HTTPException(status_code=404, detail="Queue item not found")
