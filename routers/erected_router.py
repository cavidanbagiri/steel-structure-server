from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_db
from repositories.erected_repository import ImportErectedDataRepository, FetchErectedDataRepository
from datetime import datetime, date

router = APIRouter()


# @router.post("/import_static_erected_data", status_code=status.HTTP_201_CREATED)
# async def import_static_erected_data(
#         background_tasks: BackgroundTasks,
#         db: AsyncSession = Depends(get_db)
# ):
#     try:
#         repo = ImportErectedDataRepository(db)
#         result = await repo.import_erected_main_data()
#         return result
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))





@router.post("/import_static_erected_data", status_code=201)
async def import_static_erected_data(db: AsyncSession = Depends(get_db)):
    repository = ImportErectedDataRepository(db)

    try:
        result = await repository.import_erected_data()

        return {
            "success": True,
            "message": "Erected import completed",
            "total_rows": result["total_rows"],
            "successful_imports": result["successful_imports"],
            "unmatched_rows": result["unmatched_rows"],
            "errors": result["errors"],
            "errors_count": len(result["errors"]),
            "unmatched_count": len(result["unmatched_rows"])
        }

    except Exception as ex:
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(ex)}')



@router.get("/preview_erected_data")
async def preview_erected_data(
        db: AsyncSession = Depends(get_db)
):
    try:
        excel_path = Path("static_datas/erected_data.xlsx")

        if not excel_path.exists():
            raise HTTPException(status_code=404, detail="Excel file not found")

        # Read first 5 rows for preview
        df = pd.read_excel(excel_path, nrows=5)
        total_rows = len(pd.read_excel(excel_path))

        # Check for NaN values
        full_df = pd.read_excel(excel_path)
        nan_counts = full_df.isna().sum().to_dict()

        return {
            "file_path": str(excel_path),
            "total_rows": total_rows,
            "columns": list(df.columns),
            "sample_data": df.replace({np.nan: None}).to_dict(orient='records'),
            "null_counts": {k: int(v) for k, v in nan_counts.items()},
            "file_size_mb": round(excel_path.stat().st_size / (1024 * 1024), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/fetch_erected_data", status_code=200)
async def fetch_erected_data(
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return (max 1000)"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    # Filters
    area: Optional[str] = Query(None, description="Filter by Area (exact match)"),
    structure: Optional[str] = Query(None, description="Filter by Structure (partial match)"),
    row_labels: Optional[str] = Query(None, description="Filter by Row Labels (partial match)"),
    mark_names: Optional[str] = Query(None, description="Filter by Mark Names (partial match)"),
    altitude_mark_1: Optional[str] = Query(None, description="Filter by Altitude Mark 1 (partial match)"),
    axis: Optional[str] = Query(None, description="Filter by Axis (partial match)"),
    range: Optional[str] = Query(None, description="Filter by Range (partial match)"),
    altitude_mark_2: Optional[str] = Query(None, description="Filter by Altitude Mark 2 (partial match)"),
    # Range filters
    min_e_qty: Optional[float] = Query(None, description="Minimum erected quantity"),
    max_e_qty: Optional[float] = Query(None, description="Maximum erected quantity"),
    min_e_weight: Optional[float] = Query(None, description="Minimum erected weight"),
    max_e_weight: Optional[float] = Query(None, description="Maximum erected weight"),
    min_proce_qty: Optional[float] = Query(None, description="Minimum processed quantity"),
    max_proce_qty: Optional[float] = Query(None, description="Maximum processed quantity"),
    # Date filters
    daily_e_date_from: Optional[date] = Query(None, description="Filter by date from"),
    daily_e_date_to: Optional[date] = Query(None, description="Filter by date to"),
    # Global search
    search: Optional[str] = Query(None, description="Search across multiple fields"),
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchErectedDataRepository(db)
        result = await repo.fetch_erected_data(
            limit=limit,
            offset=offset,
            area=area,
            structure=structure,
            row_labels=row_labels,
            mark_names=mark_names,
            altitude_mark_1=altitude_mark_1,
            axis=axis,
            range=range,
            altitude_mark_2=altitude_mark_2,
            min_e_qty=min_e_qty,
            max_e_qty=max_e_qty,
            min_e_weight=min_e_weight,
            max_e_weight=max_e_weight,
            min_proce_qty=min_proce_qty,
            max_proce_qty=max_proce_qty,
            daily_e_date_from=daily_e_date_from,
            daily_e_date_to=daily_e_date_to,
            search=search
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch_erected_data_unique_values", status_code=200)
async def get_erected_unique_values(
    column_name: str = Query(..., description="Column name to get unique values"),
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchErectedDataRepository(db)
        result = await repo.get_unique_values(column_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch_erected_data_statistics", status_code=200)
async def get_erected_data_statistics(
    db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchErectedDataRepository(db)
        result = await repo.get_statistics()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))