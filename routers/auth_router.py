
from typing import Annotated

from fastapi import APIRouter, Depends, Response, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from database.setup import get_db

from repositories.auth_repository import UserRegisterRepository, UserLoginRepository

from schemas import auth_schemas
from schemas.auth_schemas import UserLoginSchema

router = APIRouter()


@router.post('/register', status_code=201)
async def register(response: Response, register_data: auth_schemas.UserRegisterSchema,
                   db_session: Annotated[AsyncSession, Depends(get_db)]):
    repository = UserRegisterRepository(db_session)

    try:

        data = await repository.register(register_data)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        response.set_cookie('refresh_token', data.get('refresh_token'),
                            httponly=True,
                            secure=True,
                            samesite="none"
                            )

        return {
            'user': data.get('user'),
            'access_token': data.get('access_token')
        }

    except HTTPException as ex:
        raise ex
    except Exception as ex:
        raise HTTPException(500, 'Internal server error')





@router.post('/login', status_code=201)
async def login(response: Response, login_data: UserLoginSchema, db_session: Annotated[AsyncSession,  Depends(get_db)]):

    repository = UserLoginRepository(db_session)

    try:
        data = await repository.login(login_data)


        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        response.set_cookie('refresh_token', data.get('refresh_token'),
                            httponly=True,
                            secure=True,
                            samesite="none"
                            )
        print('the coming data is {}'.format(data))
        return {
            'user': data.get('user'),
            'access_token': data.get('access_token')
        }

    except HTTPException as ex:
        raise ex
    except Exception as ex:  # Catch all other exceptions
        raise HTTPException(500, 'Internal server error')

