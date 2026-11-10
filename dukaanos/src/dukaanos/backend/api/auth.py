"""Authentication & Onboarding Endpoints."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dukaanos.src.dukaanos.backend.database import get_db
from dukaanos.src.dukaanos.backend import models, schemas, security
from dukaanos.src.dukaanos.backend.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register-store", response_model=schemas.StoreOut)
def register_store_and_owner(
    store_in: schemas.StoreCreate,
    owner_username: str,
    owner_password: str,
    db: Session = Depends(get_db),
):
    """Registers a new retail store tenant and creates the primary owner user."""
    existing_store = db.query(models.Store).filter(models.Store.id == store_in.id).first()
    if existing_store:
        raise HTTPException(status_code=400, detail="Store ID already exists.")

    existing_user = db.query(models.User).filter(models.User.username == owner_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken.")

    store = models.Store(**store_in.model_dump())
    db.add(store)
    db.flush()

    user = models.User(
        store_id=store.id,
        username=owner_username,
        hashed_password=security.get_password_hash(owner_password),
        role="OWNER",
    )
    db.add(user)
    db.commit()
    db.refresh(store)
    return store


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticates store clerk or owner and issues JWT token."""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(
        data={"sub": user.username, "store_id": user.store_id, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "store_id": user.store_id,
        "username": user.username,
        "role": user.role,
    }


@router.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """Returns the authenticated user details."""
    return current_user

