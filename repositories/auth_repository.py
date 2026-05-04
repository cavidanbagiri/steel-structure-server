from datetime import timedelta
from typing import Union, Dict, Any

from fastapi import HTTPException
from sqlalchemy import select, delete, insert, func

from sqlalchemy.ext.asyncio import AsyncSession

from auth.token_handler import TokenHandler
from models.user_model import UserModel, TokenModel
from schemas.auth_schemas import UserLoginSchema
from utils.hash_password import PasswordHash


class RefreshTokenRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def manage_refresh_token(self, user_id:int, refresh_token) -> None:

        try:
            token = await self.find_refresh_token(user_id)
            if token:
                await self.delete_refresh_token(user_id)
            await self.save_refresh_token(user_id, refresh_token)
        except Exception as ex:
            raise HTTPException(status_code=404, detail=f'Manage refresh token error ')

    async def find_refresh_token(self, user_id: int) -> Union[TokenModel, None]:
        try:
            token = await self.db.execute(select(TokenModel).where(TokenModel.user_id == user_id))
            data = token.scalar()
            if data:
                return data
            else:
                return None
        except Exception as ex:
            raise HTTPException(status_code=404, detail=f"Refresh token not found")

    async def delete_refresh_token(self, user_id: int) -> None:
        try:
            await self.db.execute(delete(TokenModel).where(TokenModel.user_id == user_id))
        except Exception as ex:
            raise HTTPException(status_code=404, detail=f'User id not found ')

    async def save_refresh_token(self, user_id: int, refresh_token: str, access_token: str):
        try:
            token = TokenModel(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=func.now() + timedelta(days=7)
            )
            self.db.add(token)
            await self.db.commit()
        except Exception as ex:
            raise HTTPException(status_code=404, detail=f'Refresh Token can\'t save {str(ex)}')



class UserRegisterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.refresh_token_repo = RefreshTokenRepository(self.db)
        self.h_password = PasswordHash()

    # auth_repository.py - Fixed register method
    async def register(self, register_data):
        # Check email
        data = await self.db.execute(select(UserModel).where(UserModel.email == register_data.email.lower()))
        user = data.scalar()
        if user:
            raise HTTPException(status_code=409, detail="Email already exists")

        # Check username
        data = await self.db.execute(select(UserModel).where(UserModel.username == register_data.username))
        user = data.scalar()
        if user:
            raise HTTPException(status_code=409, detail="Username already exists")

        # Hash password
        register_data.password = self.h_password.hash_password(register_data.password)

        # Create user
        user = UserModel(
            firstname=register_data.firstname,
            lastname=register_data.lastname,
            username=register_data.username,
            email=register_data.email.lower(),
            password=register_data.password,
            status=register_data.status
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        token_data = {'sub': str(user.id), 'username': user.username}
        access_token = TokenHandler.generate_access_token(token_data)
        refresh_token = TokenHandler.generate_refresh_token(token_data)

        await self.refresh_token_repo.save_refresh_token(user.id, refresh_token, access_token)

        return {
            'user': {
                'id': user.id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'username': user.username,
                'email': user.email,
                'status': user.status
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }



class CheckUserAvailable:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.h_password = PasswordHash()

    async def check_user_exists(self, login_data: UserLoginSchema) -> UserModel:
        data = await self.db.execute(select(UserModel).where(UserModel.email==login_data.email.lower()))
        user = data.scalar()
        if user:
            pass_verify = self.h_password.verify(user.password, login_data.password)
            if pass_verify:
                return user
            else:
                raise HTTPException(status_code=404, detail="Password is wrong")
        else:
            raise HTTPException(status_code=404, detail="User not found")



class UserLoginRepository:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.check_user_available = CheckUserAvailable(self.db)
        self.refresh_token_repo = RefreshTokenRepository(self.db)

    # auth_repository.py - Complete login method
    async def login(self, login_data: UserLoginSchema) -> dict:
        user = await self.check_user_available.check_user_exists(login_data)

        token_data = {'sub': str(user.id), 'username': user.username}
        access_token = TokenHandler.generate_access_token(token_data)
        refresh_token = TokenHandler.generate_refresh_token(token_data)

        await self.refresh_token_repo.save_refresh_token(user.id, refresh_token, access_token)

        return {
            'user': {
                'id': user.id,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'username': user.username,
                'email': user.email,
                'status': user.status
            },
            'access_token': access_token,
            'refresh_token': refresh_token
        }

