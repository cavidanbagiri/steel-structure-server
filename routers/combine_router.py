from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_db
from repositories.combine_repository import FetchAllCombineRepository

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_all_combine_data(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    # Main filters
    main_area: Optional[str] = Query(None),
    main_zone: Optional[str] = Query(None),
    main_item: Optional[str] = Query(None),
    # Transport filters
    transport_status: Optional[str] = Query(None),
    transport_date_from: Optional[str] = Query(None),
    transport_date_to: Optional[str] = Query(None),
    # Erected filters
    erected_date_from: Optional[str] = Query(None),
    erected_date_to: Optional[str] = Query(None),
    # Global search
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    repo = FetchAllCombineRepository(db)
    try:
        result = await repo.fetch_all_combine_data(
            limit=limit,
            offset=offset,
            main_area=main_area,
            main_zone=main_zone,
            main_item=main_item,
            transport_status=transport_status,
            transport_date_from=transport_date_from,
            transport_date_to=transport_date_to,
            erected_date_from=erected_date_from,
            erected_date_to=erected_date_to,
            search=search,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))