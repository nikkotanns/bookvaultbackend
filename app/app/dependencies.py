from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.services import UsersService, CollectionsService, BooksService
from app.schemas import UserRead
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

async def get_users_service(db: AsyncSession = Depends(get_db)) -> UsersService:
    return UsersService(db)

async def get_collections_service(db: AsyncSession = Depends(get_db)) -> CollectionsService:
    return CollectionsService(db)

async def get_books_service(db: AsyncSession = Depends(get_db)) -> BooksService:
    return BooksService(db)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/swaggertoken")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UsersService = Depends(get_users_service)
) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await service.get_user(login)
    if user is None:
        raise credentials_exception
    return UserRead.model_validate(user)
