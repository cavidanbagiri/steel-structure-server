from datetime import date
from typing import Optional
from pydantic import BaseModel


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_db

from repositories.transport_repository import ImportTransportDataRepository, FetchTransportDataRepository, \
    TransportWriteRepository

router = APIRouter()


@router.post("/import_static_transport_data", status_code=201)
async def import_static_transport_data(db: AsyncSession = Depends(get_db)):
    repository = ImportTransportDataRepository(db)

    try:
        result = await repository.import_transport_data()

        return {
            "message": "Import completed",
            "total_rows_processed": result["total_rows"],
            "successful_imports": result["successful_imports"],
            "failed_rows": result["failed_rows"],
            "errors_file": result.get("errors_file")
        }

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')


@router.get("/fetch_transport_data", status_code=200)
async def fetch_transport_data(
        limit: int = Query(100, ge=1, le=1000, description="Number of records to return (max 1000)"),
        offset: int = Query(0, ge=0, description="Number of records to skip"),
        # Filters
        structure_1: Optional[str] = Query(None, description="Filter by Structure 1"),
        structure_2: Optional[str] = Query(None, description="Filter by Structure 2"),
        mark_name: Optional[str] = Query(None, description="Filter by Mark Name (partial match)"),
        order_no: Optional[str] = Query(None, description="Filter by Order No (partial match)"),
        area: Optional[str] = Query(None, description="Filter by Area"),
        location: Optional[str] = Query(None, description="Filter by Location"),
        t_status: Optional[str] = Query(None, description="Filter by Transport Status"),
        t_date_from: Optional[date] = Query(None, description="Filter by date from"),
        t_date_to: Optional[date] = Query(None, description="Filter by date to"),
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
            mark_name=mark_name,
            order_no=order_no,
            area=area,
            location=location,
            t_status=t_status,
            t_date_from=t_date_from,
            t_date_to=t_date_to,
            min_weight=min_weight,
            max_weight=max_weight,
            search=search
        )

        return result

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')


@router.get("/fetch_transport_data/{transport_id}", status_code=200)
async def fetch_transport_by_id(
        transport_id: int,
        db: AsyncSession = Depends(get_db)
):
    repository = FetchTransportDataRepository(db)

    try:
        result = await repository.get_transport_by_id(transport_id)

        if not result:
            raise HTTPException(404, f"Transport with ID {transport_id} not found")

        return result

    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')


@router.get("/unique_values/{column_name}", status_code=200)
async def get_unique_values(
        column_name: str,
        db: AsyncSession = Depends(get_db)
):
    """Get unique values for a column (useful for filter dropdowns)"""
    repository = FetchTransportDataRepository(db)

    # Allowed column names for security
    allowed_columns = [
        "structure_1", "structure_2", "area", "location",
        "t_status", "mark_name"
    ]

    if column_name not in allowed_columns:
        raise HTTPException(400, f"Column '{column_name}' is not allowed")

    try:
        result = await repository.get_unique_values(column_name)
        return {column_name: result}

    except Exception as ex:
        raise HTTPException(500, f'Internal server error: {str(ex)}')




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


