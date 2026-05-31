from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserResponse, UpdateProfileRequest


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user: User) -> UserResponse:
        return UserResponse.model_validate(user)

    def update_profile(self, user: User, data: UpdateProfileRequest) -> UserResponse:
        if data.full_name is not None:
            user.full_name = data.full_name
        self.db.commit()
        self.db.refresh(user)
        return UserResponse.model_validate(user)
