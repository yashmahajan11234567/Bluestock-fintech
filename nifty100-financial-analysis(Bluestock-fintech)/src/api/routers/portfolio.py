"""Portfolio router scaffold."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/portfolio")
async def portfolio():
    """Retrieve portfolio summary for the authenticated user."""
    return {"message": "Not implemented yet", "endpoint": "/api/v1/portfolio"}
