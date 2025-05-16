from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from app.dependencies import (
    get_users_service,
    get_collections_service,
    get_books_service,
    get_current_user
)
from app.schemas import (
    UserCreate, UserRead,
    CollectionCreate, CollectionRead, CollectionReadWithBooks,
    BookCreate, BookRead
)
from app.services import UsersService, CollectionsService, BooksService
from uuid import UUID
from app.utils import verify_password, create_access_token, hash_password
from app.database import get_s3_client
from app.config import settings
from unidecode import unidecode

router = APIRouter()

def check_ownership(current_user: UserRead, resource_owner: str):
    if current_user.login != resource_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )


# Auth Endpoints
@router.post("/auth/token")
async def login_for_access_token(
    user_data: UserCreate,
    service: UsersService = Depends(get_users_service)
):
    user = await service.get_user(user_data.login)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password"
        )
    access_token = create_access_token(data={"sub": user.login})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/swaggertoken")
async def login_for_swagger_token(
    username: str = Form(...),
    password: str = Form(...),
    service: UsersService = Depends(get_users_service)
):
    user = await service.get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password"
        )
    access_token = create_access_token(data={"sub": user.login})
    return {"access_token": access_token, "token_type": "bearer"}

# User Endpoints
@router.post("/users/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UsersService = Depends(get_users_service)
):
    hashed_password = hash_password(user_data.password)
    user = await service.create_user(user_data.login, hashed_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    await service.session.commit()
    return user

@router.get("/users/{login}", response_model=UserRead)
async def get_user(
    login: str,
    service: UsersService = Depends(get_users_service),
    current_user: UserRead = Depends(get_current_user),
):
    check_ownership(current_user, login)
    user = await service.get_user(login)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/users/{login}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    login: str,
    service: UsersService = Depends(get_users_service),
    current_user: UserRead = Depends(get_current_user),
):
    check_ownership(current_user, login)
    success = await service.delete_user(login)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    await service.session.commit()

# Collections Endpoints
@router.post(
    "/users/{user_login}/collections/",
    response_model=CollectionRead,
    status_code=status.HTTP_201_CREATED
)
async def create_collection(
    user_login: str,
    collection_data: CollectionCreate,
    service: CollectionsService = Depends(get_collections_service),
    current_user: UserRead = Depends(get_current_user),
):
    check_ownership(current_user, user_login)
    collection = await service.create_collection(
        name=collection_data.name,
        user_login=user_login
    )
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    await service.session.commit()
    return collection

@router.get("/collections/{uuid}", response_model=CollectionReadWithBooks)
async def get_collection(
    uuid: UUID,
    service: CollectionsService = Depends(get_collections_service),
    current_user: UserRead = Depends(get_current_user),
):
    collection = await service.get_collection(uuid)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    check_ownership(current_user, collection.user_login)
    return collection

@router.get("/users/{user_login}/collections/", response_model=list[CollectionRead])
async def get_user_collections(
    user_login: str,
    service: CollectionsService = Depends(get_collections_service),
    current_user: UserRead = Depends(get_current_user),
):
    check_ownership(current_user, user_login)
    collections = await service.get_user_collections(user_login)
    return collections

@router.delete("/collections/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    uuid: UUID,
    service: CollectionsService = Depends(get_collections_service),
    current_user: UserRead = Depends(get_current_user),
):
    collection = await service.get_collection(uuid)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    check_ownership(current_user, collection.user_login)
    await service.delete_collection(uuid)
    await service.session.commit()

# Books Endpoints
@router.post(
    "/collections/{collection_uuid}/books/",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED
)
async def create_book(
    collection_uuid: UUID,
    book_data: BookCreate,
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    # Получаем коллекцию через CollectionsService
    collection = await collections_service.get_collection(collection_uuid)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    check_ownership(current_user, collection.user_login)
    
    # Создаем книгу через BooksService
    book = await books_service.create_book(
        title=book_data.title,
        author=book_data.author,
        description=book_data.description,
        collection_uuid=collection_uuid
    )
    await books_service.session.commit()
    return book


@router.put("/books/{book_uuid}/file", response_model=BookRead)
async def upload_book_file(
    book_uuid: UUID,
    file: UploadFile = File(...),
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    book = await books_service.get_book(book_uuid)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    collection = await collections_service.get_collection(book.collection_uuid)
    check_ownership(current_user, collection.user_login)

    try:
        # Преобразуем имя файла в ASCII
        filename_ascii = unidecode(file.filename)
        
        file_key = f"books/{book.uuid}"
        async with get_s3_client() as s3:
            await s3.upload_fileobj(
                Fileobj=file.file,
                Bucket=settings.bucket_name,
                Key=file_key
            )

        updated_book = await books_service.update_file_name(
            book_uuid=book.uuid,
            file_name=filename_ascii  # Используем преобразованное имя
        )
        await books_service.session.commit()
        return updated_book

    except Exception as e:
        await books_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/books/{book_uuid}/file")
async def download_book_file(
    book_uuid: UUID,
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    book = await books_service.get_book(book_uuid)
    if not book or not book.file_name:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Получаем коллекцию через CollectionsService
    collection = await collections_service.get_collection(book.collection_uuid)
    check_ownership(current_user, collection.user_login)

    try:
        file_key = f"books/{book.uuid}"
        async with get_s3_client() as s3:
            obj = await s3.get_object(
                Bucket=settings.bucket_name,
                Key=file_key
            )
            data = await obj["Body"].read()

        return StreamingResponse(
            iter([data]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={book.file_name}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File download error: {str(e)}"
        )

@router.get("/books/{uuid}", response_model=BookRead)
async def get_book(
    uuid: UUID,
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    book = await books_service.get_book(uuid)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Получаем коллекцию через CollectionsService
    collection = await collections_service.get_collection(book.collection_uuid)
    check_ownership(current_user, collection.user_login)
    return book

@router.get("/collections/{collection_uuid}/books/", response_model=list[BookRead])
async def get_collection_books(
    collection_uuid: UUID,
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    # Получаем коллекцию через CollectionsService
    collection = await collections_service.get_collection(collection_uuid)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    check_ownership(current_user, collection.user_login)
    
    # Получаем книги через BooksService
    books = await books_service.get_collection_books(collection_uuid)
    return books

@router.put("/books/{uuid}", response_model=BookRead)
async def update_book(
    uuid: UUID,
    book_data: BookCreate,
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    book = await books_service.get_book(uuid)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Получаем коллекцию через CollectionsService
    collection = await collections_service.get_collection(book.collection_uuid)
    check_ownership(current_user, collection.user_login)
    
    updated_book = await books_service.update_book(
        uuid,
        title=book_data.title,
        author=book_data.author,
        description=book_data.description
    )
    await books_service.session.commit()
    return updated_book


@router.delete("/books/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    uuid: UUID,
    collections_service: CollectionsService = Depends(get_collections_service),
    books_service: BooksService = Depends(get_books_service),
    current_user: UserRead = Depends(get_current_user),
):
    book = await books_service.get_book(uuid)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    collection = await collections_service.get_collection(book.collection_uuid)
    check_ownership(current_user, collection.user_login)

    file_key = f"books/{book.uuid}"

    try:
        async with get_s3_client() as s3:
            if book.file_name:
                await s3.delete_object(
                    Bucket=settings.bucket_name,
                    Key=file_key
                )
    except Exception as e:
        pass

    await books_service.delete_book(uuid)
    await books_service.session.commit()