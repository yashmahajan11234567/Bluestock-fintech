"""Documents router scaffold."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/documents")
async def documents():
    """Retrieve documents list for the authenticated user."""
    return {"message": "Not implemented yet", "endpoint": "/api/v1/documents"}
