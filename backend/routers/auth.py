import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from database import get_connection
from dependencies import get_current_user
from models import LoginRequest, SignupRequest, TokenResponse, UserResponse
from security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    email = payload.email.lower()
    password_hash = hash_password(payload.password)
    try:
        with get_connection() as conn:
            row = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) "
                "RETURNING id, email, created_at",
                (email, password_hash),
            ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    return row
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    email = payload.email.lower()
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = %s", (email,)
        ).fetchone()
    stored_hash = user["password_hash"] if user else DUMMY_HASH
    password_ok = verify_password(payload.password, stored_hash)
    if user is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user["id"]))


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user