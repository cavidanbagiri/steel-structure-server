from datetime import date
from typing import Optional
from pydantic import BaseModel


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_db

from repositories.transport_repository import ImportTransportDataRepository, FetchTransportDataRepository, \
    TransportWriteRepository, GetTransportByIdRepository, InsertToErectedRepository


from schemas.transport_schema import InsertErectedSchema

router = APIRouter()

#
# @router.post("/import_static_transport_data", status_code=201)
# async def import_static_transport_data(db: AsyncSession = Depends(get_db)):
#     repository = ImportTransportDataRepository(db)
#
#     try:
#         result = await repository.import_transport_data()
#
#         return {
#             "message": "Import completed",
#             "total_rows_processed": result["total_rows"],
#             "successful_imports": result["successful_imports"],
#             "failed_rows": result["failed_rows"],
#             "errors_file": result.get("errors_file")
#         }
#
#     except Exception as ex:
#         raise HTTPException(500, f'Internal server error: {str(ex)}')

@router.post("/import_static_transport_data", status_code=201)
async def import_static_transport_data(db: AsyncSession = Depends(get_db)):
    repository = ImportTransportDataRepository(db)

    try:
        result = await repository.import_transport_data()

        return {
            "success": True,
            "message": "Transport import completed",
            "total_rows": result["total_rows"],
            "successful_imports": result["successful_imports"],
            "errors": result["errors"],
            "errors_count": len(result["errors"])
        }

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(ex)}')

@router.get("/fetch_transport_data", status_code=200)
async def fetch_transport_data(
        limit: int = Query(100, ge=1, le=1000, description="Number of records to return (max 1000)"),
        offset: int = Query(0, ge=0, description="Number of records to skip"),
        # Filters
        structure_1: Optional[str] = Query(None, description="Filter by Structure 1"),
        structure_2: Optional[str] = Query(None, description="Filter by Structure 2"),
        raw_labels: Optional[str] = Query(None, description="Filter by Row Labels"),
        mark_name: Optional[str] = Query(None, description="Filter by Mark Name (partial match)"),
        order_no: Optional[str] = Query(None, description="Filter by Order No (partial match)"),
        area: Optional[str] = Query(None, description="Filter by Area"),
        location: Optional[str] = Query(None, description="Filter by Location"),
        key: Optional[str] = Query(None, description="Filter by Key"),
        t_status: Optional[str] = Query(None, description="Filter by Transport Status"),
        t_date_from: Optional[date] = Query(None, description="Filter by date from"),
        t_date_to: Optional[date] = Query(None, description="Filter by date to"),
        t_qty: Optional[float] = Query(None, description="Filter by Transport Quantity"),
        t_weight: Optional[float] = Query(None, description="Filter by Transport Weight"),
        t_leftover_qty: Optional[float] = Query(None, description="Filter by Transport Leftover Quantity"),
        proce_qty: Optional[float] = Query(None, description="Filter by Transport Proce Quantity"),
        min_weight: Optional[float] = Query(None, description="Minimum weight"),
        max_weight: Optional[float] = Query(None, description="Maximum weight"),
        search: Optional[str] = Query(None, description="Search across multiple fields"),
        db: AsyncSession = Depends(get_db)
):
    repository = FetchTransportDataRepository(db)

    try:
        result = await repository.fetch_transport_data(
            limit=limit,
            offset=offset,
            structure_1=structure_1,
            structure_2=structure_2,
            raw_labels=raw_labels,
            mark_name=mark_name,
            order_no=order_no,
            area=area,
            location=location,
            key=key,
            t_status=t_status,
            t_date_from=t_date_from,
            t_date_to=t_date_to,
            t_qty = t_qty,
            t_weight = t_weight,
            t_leftover_qty = t_leftover_qty,
            proce_qty = proce_qty,
            min_weight=min_weight,
            max_weight=max_weight,
            search=search
        )

        return result

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')


@router.get("/{id}", status_code=200)
async def get_transport_by_id(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = GetTransportByIdRepository(db, id)
        result = await repo.get_transport_by_id()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/unique_values/{column_name}", status_code=200)
async def get_unique_values(
    column_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get unique values for filters"""

    repository = FetchTransportDataRepository(db)

    allowed_columns = [
        "structure_1",
        "area",
        "location",
        "t_status"
    ]

    if column_name not in allowed_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Column '{column_name}' is not allowed"
        )

    try:
        result = await repository.get_unique_values(column_name)

        return {
            "success": True,
            "column": column_name,
            "values": result
        }

    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(ex)}"
        )



#
# @router.get("/unique_values/{column_name}", status_code=200)
# async def get_unique_values(
#         column_name: str,
#         db: AsyncSession = Depends(get_db)
# ):
#     """Get unique values for a column (useful for filter dropdowns)"""
#     repository = FetchTransportDataRepository(db)
#
#     # Allowed column names for security
#     allowed_columns = [
#         "structure_1", "area", "location",
#         "t_status"
#     ]
#
#     if column_name not in allowed_columns:
#         raise HTTPException(400, f"Column '{column_name}' is not allowed")
#
#     try:
#         result = await repository.get_unique_values(column_name)
#         return {column_name: result}
#
#     except Exception as ex:
#         raise HTTPException(500, f'Internal server error: {str(ex)}')
#



# Define request schemas
class TransportCreateRequest(BaseModel):
    structure_1: Optional[str] = None
    structure_2: Optional[str] = None
    raw_labels: Optional[str] = None
    mark_name: Optional[str] = None
    t_qty: Optional[float] = None
    t_weight: Optional[float] = None
    t_date: Optional[date] = None
    t_status: Optional[str] = None
    proce_qty: Optional[int] = None
    order_no: Optional[str] = None
    key: Optional[str] = None
    area: Optional[str] = None
    location: Optional[str] = None


class TransportUpdateRequest(BaseModel):
    structure_1: Optional[str] = None
    structure_2: Optional[str] = None
    raw_labels: Optional[str] = None
    mark_name: Optional[str] = None
    t_qty: Optional[float] = None
    t_weight: Optional[float] = None
    t_date: Optional[date] = None
    t_status: Optional[str] = None
    proce_qty: Optional[int] = None
    order_no: Optional[str] = None
    key: Optional[str] = None
    area: Optional[str] = None
    location: Optional[str] = None


@router.post("/create_transport", status_code=201)
async def create_transport(
        data: TransportCreateRequest,
        db: AsyncSession = Depends(get_db)
):
    repository = TransportWriteRepository(db)

    try:
        # Convert request to dict
        transport_data = data.dict(exclude_unset=True)
        # You can set created_by to None or a default user ID if needed
        transport_data['created_by'] = None  # Or remove this line entirely

        result = await repository.create_transport(transport_data)

        return {
            "message": "Transport created successfully",
            "data": result
        }

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')


@router.put("/update_transport/{transport_id}", status_code=200)
async def update_transport(
        transport_id: int,
        data: TransportUpdateRequest,
        db: AsyncSession = Depends(get_db)
):
    repository = TransportWriteRepository(db)

    try:
        # Only update fields that are provided
        update_data = {k: v for k, v in data.dict().items() if v is not None}

        result = await repository.update_transport(transport_id, update_data)

        return {
            "message": "Transport updated successfully",
            "data": result
        }

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')


@router.delete("/delete_transport/{transport_id}", status_code=200)
async def delete_transport(
        transport_id: int,
        db: AsyncSession = Depends(get_db)
):
    repository = TransportWriteRepository(db)

    try:
        await repository.delete_transport(transport_id)

        return {
            "message": "Transport deleted successfully"
        }

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')





@router.post("/insert_to_erected", status_code=201)
async def insert_to_erected(
    insert_data: InsertErectedSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = InsertToErectedRepository(db, insert_data)
        result = await repo.insert_to_erected()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




