from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlmodel import Session, select, col
from typing import List
from jose import jwt, JWTError
from contextlib import asynccontextmanager

import sys
import os
from pathlib import Path

# Adiciona o diretório src ao path para importações relativas funcionarem
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .database import get_session, create_db_and_tables
from .models import User, UserCreate, HistoryItem, HistoryItemCreate
from .auth import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM
from ..downloader.video_downloader import VideoDownloader


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="YouTube Music Pro Sync API", lifespan=lifespan)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


# --- Auth Dependencies ---
async def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user


# --- Routes ---


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username}


@app.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/history", response_model=List[HistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    limit: int = 20,
    offset: int = 0,
):
    history = session.exec(
        select(HistoryItem)
        .where(HistoryItem.user_id == current_user.id)
        .order_by(col(HistoryItem.timestamp).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return history


@app.post("/history", status_code=status.HTTP_201_CREATED)
def add_to_history(
    item_data: HistoryItemCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if current_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User identification failed: ID missing",
        )
    new_item = HistoryItem(**item_data.model_dump(), user_id=current_user.id)
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return new_item


@app.get("/")
def read_root():
    return {"message": "YouTube Music Pro Sync API is online", "docs": "/docs"}


from fastapi.responses import FileResponse
from pydantic import BaseModel


class DownloadRequest(BaseModel):
    url: str
    mode: str = "audio"  # or video
    audio_format: str = "mp3"
    audio_quality: str = "192k"
    video_quality: str = "720p"


@app.post("/download")
def download_content(request: DownloadRequest):
    download_dir = Path("/tmp/youtube_downloader_mobile")
    download_dir.mkdir(parents=True, exist_ok=True)

    # Limpa downloads antigos (opcional)
    for old_file in download_dir.glob("*"):
        try:
            old_file.unlink()
        except Exception:
            pass

    downloader = VideoDownloader(output_dir=str(download_dir))

    if request.mode == "video":
        ok, message, _ = downloader.download_video(request.url, video_quality=request.video_quality)
        media_type = "video/mp4"
    else:
        ok, message, _ = downloader.download_audio(
            request.url,
            audio_format=request.audio_format,
            audio_quality=request.audio_quality,
        )
        media_type = "audio/mpeg" if request.audio_format == "mp3" else "audio/ogg"

    if not ok:
        raise HTTPException(status_code=400, detail=message)

    files = sorted(download_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise HTTPException(status_code=500, detail="Arquivo não encontrado após download")

    result_file = files[0]
    return FileResponse(
        path=str(result_file),
        filename=result_file.name,
        media_type=media_type,
    )
