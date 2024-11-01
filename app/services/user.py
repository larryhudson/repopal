 from sqlalchemy.orm import Session
 from app.repositories.user import UserRepository
 from app.schemas.user import UserCreate, User

 class UserService:
     def __init__(self):
         self.repository = UserRepository()

     def create_user(self, db: Session, user: UserCreate) -> User:
         return self.repository.create(db, obj_in=user)

     def get_user(self, db: Session, user_id: int) -> User | None:
         return self.repository.get(db, id=user_id)
