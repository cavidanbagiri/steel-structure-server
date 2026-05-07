
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from database.setup import get_db

from repositories.main_data_repository import ImportMainDataRepository

router = APIRouter()


@router.post("/import_static_main_data", status_code=201)
async def import_statis_main_data(
        db: AsyncSession = Depends(get_db)
):
    try:
        repo = ImportMainDataRepository(db)

        result = await repo.import_static_main_data()


    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

