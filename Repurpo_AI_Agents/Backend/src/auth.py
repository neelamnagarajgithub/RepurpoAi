# backend/auth.py
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from Backend.src.db import AsyncSessionLocal, init_db
from Backend.src import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
# near top of file: keep MAX_PASSWORD_BYTES definition
MAX_PASSWORD_BYTES = 72

def _password_byte_length_ok(password: str) -> bool:
    # bcrypt limit is 72 bytes; use utf-8 encoding to compute byte-length
    try:
        return len(password.encode("utf-8")) <= MAX_PASSWORD_BYTES
    except Exception:
        return False

# ----------------- New helper: canonicalize/truncate password -----------------
def _truncate_password_by_bytes(password: str) -> str:
    """
    Truncate the provided password to MAX_PASSWORD_BYTES when encoded as utf-8.
    Returns a valid utf-8 str (may drop partial multibyte at the end).
    This ensures bcrypt (72-byte) limit is never exceeded while keeping behavior
    consistent between hash and verify.
    """
    if password is None:
        return password
    try:
        b = password.encode("utf-8")
    except Exception:
        # Fallback: force str then encode
        b = str(password).encode("utf-8", errors="ignore")
    if len(b) <= MAX_PASSWORD_BYTES:
        return password
    tb = b[:MAX_PASSWORD_BYTES]
    return tb.decode("utf-8", errors="ignore")

# ----------------- Replace get_password_hash / verify_password -----------------
def verify_password(plain, hashed) -> bool:
    # Truncate the incoming plain password consistently before verify
    if plain is None or hashed is None:
        return False
    return pwd_context.verify(_truncate_password_by_bytes(plain), hashed)

def get_password_hash(password) -> str:
    # Truncate password before hashing to avoid bcrypt ValueError
    return pwd_context.hash(_truncate_password_by_bytes(password))

router = APIRouter()

# Utilities
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    q = select(models.User).where(models.User.email == email)
    res = await db.execute(q)
    return res.scalar_one_or_none()

async def create_user(db: AsyncSession, email: str, password: str) -> models.User:
    user = models.User(email=email, hashed_password=get_password_hash(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[models.User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

# Routes
@router.post("/auth/signup", response_model=dict)
async def signup(item: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # validate password length in bytes
    if not _password_byte_length_ok(item.password):
        raise HTTPException(
            status_code=400,
            detail=f"Password is too long when encoded (max {MAX_PASSWORD_BYTES} bytes). "
                   "Use a shorter password (or pre-hash client-side) and try again."
        )

    existing = await get_user_by_email(db, item.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await create_user(db, item.email, item.password)
    return {"id": user.id, "email": user.email}

@router.post("/auth/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # form_data.username is email
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials", headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Messages
@router.post("/messages", response_model=schemas.MessageOut)
async def post_message(payload: schemas.MessageCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv_id = payload.conversation_id
    # create conversation if none provided
    if conv_id is None:
        conv = models.Conversation(user_id=current_user.id, title=(payload.content[:120] if payload.content else None))
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    msg = models.Message(user_id=current_user.id, conversation_id=conv_id, role=payload.role, content=payload.content, meta=payload.meta)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

@router.get("/messages", response_model=list[schemas.MessageOut])
async def list_messages(limit: int = 100, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Message).where(models.Message.user_id == current_user.id).order_by(models.Message.created_at.desc()).limit(limit)
    res = await db.execute(q)
    rows = res.scalars().all()
    return rows

# Downloads
@router.post("/downloads", response_model=schemas.DownloadOut)
async def post_download(payload: schemas.DownloadCreate, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    d = models.Download(user_id=current_user.id, filename=payload.filename, url=payload.url, meta=payload.meta)
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d

@router.get("/downloads", response_model=list[schemas.DownloadOut])
async def list_downloads(limit: int = 100, current_user: models.User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(models.Download).where(models.Download.user_id == current_user.id).order_by(models.Download.created_at.desc()).limit(limit)
    res = await db.execute(q)
    rows = res.scalars().all()
    return rows