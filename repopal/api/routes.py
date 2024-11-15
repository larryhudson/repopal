from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from repopal.core.database import get_db
from repopal.schemas.user import User, UserCreate
from repopal.services.user import UserService

router = APIRouter()
user_service = UserService()


@router.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db=db, user=user)


@router.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user(db=db, user_id=user_id)
