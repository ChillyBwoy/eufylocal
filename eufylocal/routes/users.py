from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError

from eufylocal.di import UserRepositoryDep
from eufylocal.schemas.user import User, UserCreate, UserUpdate

router = APIRouter(tags=["users"], prefix="/users")


@router.get("/", response_model=list[User], operation_id="get_users")
async def users(repository: UserRepositoryDep) -> list[User]:
    items = await repository.list()
    return [User.model_validate(item) for item in items]


@router.post(
    "/",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    operation_id="create_user",
)
async def create_user(payload: UserCreate, repository: UserRepositoryDep) -> User:
    try:
        user = await repository.create(name=payload.name, color=payload.color)
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User name already exists",
        ) from error
    return User.model_validate(user)


@router.patch("/{user_id}", response_model=User, operation_id="update_user")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    repository: UserRepositoryDep,
) -> User:
    try:
        user = await repository.update(
            user_id,
            name=payload.name,
            color=payload.color,
        )
    except IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User name already exists",
        ) from error
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return User.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_user",
)
async def delete_user(user_id: int, repository: UserRepositoryDep) -> Response:
    if not await repository.delete(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
