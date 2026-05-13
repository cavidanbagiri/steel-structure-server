
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query

from sqlalchemy.ext.asyncio import AsyncSession

from database.setup import get_db

from repositories.statistic_repository import FetchMainDataProjectStatisticsRepository

router = APIRouter()



@router.get("/fetch_main_data_project_statistics", status_code=200)
async def fetch_main_data_project_statistics(
        db: AsyncSession = Depends(get_db)
):
    try:
        repo = FetchMainDataProjectStatisticsRepository(db)
        result = await repo.fetch_main_data_project_statistics()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

