from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query

from sqlalchemy.ext.asyncio import AsyncSession

from database.setup import get_db

from repositories.main_data_repository import ImportMainDataRepository, FetchMainDataRepository, GetRowByIdRepository, InsertToTransportRepository
from schemas.main_schema import InsertTransportSchema

router = APIRouter()

#
# @router.post("/import_static_main_data", status_code=status.HTTP_201_CREATED)
# async def import_static_main_data(
#         background_tasks: BackgroundTasks,
#         use_batch_method: bool = False,
#         db: AsyncSession = Depends(get_db)
# ):
#     try:
#         repo = ImportMainDataRepository(db)
#
#         # Run import in background for large files
#         if use_batch_method:
#             result = await repo.import_static_main_data_batch()
#         else:
#             result = await repo.import_static_main_data()
#
#         return result
#
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


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
    qty: Optional[float] = Query(None, description="Quantity"),
    length: Optional[float] = Query(None, description="Length"),
    weight: Optional[float] = Query(None, description="Weight"),
    weight_total: Optional[float] = Query(None, description="Total weight"),
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
            qty=qty,
            length=length,
            weight=weight,
            weight_total=weight_total,
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



@router.get("/{id}", status_code=200)
async def get_row_by_id(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = GetRowByIdRepository(db, id)
        result = await repo.get_row_by_id()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/insert_to_transport", status_code=201)
async def insert_to_transport(
    insert_data: InsertTransportSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        print(insert_data.qty)
        repo = InsertToTransportRepository(db, insert_data)
        result = await repo.insert_to_transport()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))













