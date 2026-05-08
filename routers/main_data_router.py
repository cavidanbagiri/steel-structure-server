from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query

from sqlalchemy.ext.asyncio import AsyncSession

from database.setup import get_db

from repositories.main_data_repository import ImportMainDataRepository, FetchMainDataRepository

router = APIRouter()


@router.post("/import_static_main_data", status_code=status.HTTP_201_CREATED)
async def import_static_main_data(
        background_tasks: BackgroundTasks,
        use_batch_method: bool = False,
        db: AsyncSession = Depends(get_db)
):
    try:
        repo = ImportMainDataRepository(db)

        # Run import in background for large files
        if use_batch_method:
            result = await repo.import_static_main_data_batch()
        else:
            result = await repo.import_static_main_data()

        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview_static_data")
async def preview_static_data(
        db: AsyncSession = Depends(get_db)
):
    try:
        repo = ImportMainDataRepository(db)
        preview = await repo.preview_file_info()
        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/fetch_main_data", status_code=200)
async def fetch_main_data(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return (max 1000)"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    # Filters
    area: Optional[str] = Query(None, description="Filter by Area (exact match)"),
    zone: Optional[str] = Query(None, description="Filter by Zone (exact match)"),
    key: Optional[str] = Query(None, description="Filter by Key (partial match)"),
    row_labels: Optional[str] = Query(None, description="Filter by Row Labels (partial match)"),
    item: Optional[str] = Query(None, description="Filter by Item (partial match)"),
    p_s: Optional[str] = Query(None, description="Filter by P/S (exact match)"),
    section: Optional[str] = Query(None, description="Filter by Section (partial match)"),
    dwgn: Optional[str] = Query(None, description="Filter by DWGN (partial match)"),
    # Range filters
    min_qty: Optional[float] = Query(None, description="Minimum quantity"),
    max_qty: Optional[float] = Query(None, description="Maximum quantity"),
    min_length: Optional[float] = Query(None, description="Minimum length"),
    max_length: Optional[float] = Query(None, description="Maximum length"),
    min_weight: Optional[float] = Query(None, description="Minimum weight"),
    max_weight: Optional[float] = Query(None, description="Maximum weight"),
    min_weight_total: Optional[float] = Query(None, description="Minimum total weight"),
    max_weight_total: Optional[float] = Query(None, description="Maximum total weight"),
    # Global search
    search: Optional[str] = Query(None, description="Search across multiple fields"),
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchMainDataRepository(db)
        result = await repo.fetch_main_data(
            limit=limit,
            offset=offset,
            area=area,
            zone=zone,
            key=key,
            row_labels=row_labels,
            item=item,
            p_s=p_s,
            section=section,
            dwgn=dwgn,
            min_qty=min_qty,
            max_qty=max_qty,
            min_length=min_length,
            max_length=max_length,
            min_weight=min_weight,
            max_weight=max_weight,
            min_weight_total=min_weight_total,
            max_weight_total=max_weight_total,
            search=search
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch_main_data_unique_values", status_code=200)
async def get_unique_values(
    column_name: str = Query(..., description="Column name to get unique values"),
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchMainDataRepository(db)
        result = await repo.get_unique_values(column_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch_main_data_statistics", status_code=200)
async def get_main_data_statistics(
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchMainDataRepository(db)
        result = await repo.get_statistics()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))