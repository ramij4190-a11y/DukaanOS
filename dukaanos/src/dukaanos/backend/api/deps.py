"""FastAPI Request Dependencies & Tenant Context Resolution."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Enforces authentication and extracts tenant (store_id) context."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    store_id: str = payload.get("store_id")
    if username is None or store_id is None:
        raise credentials_exception

    user = db.query(models.User).filter(
        models.User.username == username,
        models.User.store_id == store_id,
    ).first()

    if user is None:
        raise credentials_exception

    return user

