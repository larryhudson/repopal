from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from repopal.core.config import settings

# TODO: missing / incorrect import
from repopal.core.database import get_db

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://github.com/login/oauth/authorize",
    tokenUrl="https://github.com/login/oauth/access_token",
)


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Optional[dict]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # TODO: Here you would typically query your user from the database
    # For now returning the decoded payload
    return payload
