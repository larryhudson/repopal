 from app.repositories.base import BaseRepository
 from app.models.user import User

 class UserRepository(BaseRepository[User]):
     def __init__(self):
         super().__init__(User)
