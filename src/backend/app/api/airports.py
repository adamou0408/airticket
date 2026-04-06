"""Airport search API.

US-12: Global airport search
"""

from fastapi import APIRouter, Query
from app.airports.service import search_airports, get_airport, get_all_airports, get_airport_count

router = APIRouter(prefix="/airports", tags=["airports"])


@router.get("")
async def search(q: str = Query("", description="Search query (IATA code, city, country — zh or en)"), limit: int = 20):
    """Search airports. Empty query returns popular airports."""
    results = search_airports(q, limit)
    return {"results": results, "count": len(results)}


@router.get("/all")
async def get_all():
    """Get all airports (for frontend local search). ~1MB JSON."""
    airports = get_all_airports()
    return {"airports": airports, "count": len(airports)}


@router.get("/count")
async def count():
    return {"count": get_airport_count()}


@router.get("/{iata}")
async def get_by_code(iata: str):
    airport = get_airport(iata)
    if not airport:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Airport {iata} not found")
    return airport
