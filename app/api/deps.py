from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User


def get_optional_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.startswith('Bearer '):
        return None
    token = authorization.split(' ', 1)[1]
    user_id = decode_token(token)
    if not user_id:
        return None
    return db.get(User, int(user_id))


def get_current_user(user: Optional[User] = Depends(get_optional_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    return user
