from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from sqlmodel import Session, select, col
from typing import List
from jose import jwt, JWTError
from contextlib import asynccontextmanager

import sys
import os
import uuid
import threading
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

# Store de progresso de downloads para polling em tempo real
download_progress = {}

# Store de controle de tarefas (cancelamento)
download_tasks = {}

# Estrutura de cada entry:
# {"status": "pending|running|done|error", "percent": float, "message": str, "file": Path|None}


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


from pydantic import BaseModel


class DownloadRequest(BaseModel):
    url: str
    mode: str = "audio"  # or video
    audio_format: str = "mp3"
    audio_quality: str = "192k"
    video_quality: str = "720p"


def _safe_filename(title: str, ext: str) -> str:
    name = title.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")
    name = "".join(c for c in name if c.isalnum() or c in "._-")
    if not name:
        name = "downloaded_media"
    return f"{name}.{ext}"


def _run_download_task(task_id: str, request: DownloadRequest):
    base_download_dir = Path("/tmp/youtube_downloader_mobile")
    base_download_dir.mkdir(parents=True, exist_ok=True)
    task_dir = base_download_dir / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    progress = download_progress[task_id]
    cancel_event = download_tasks.get(task_id, {}).get("cancel_event")

    def progress_callback(info):
        if cancel_event and cancel_event.is_set():
            if download_tasks.get(task_id, {}).get("downloader"):
                download_tasks[task_id]["downloader"].stop()
            progress.update({"status": "error", "message": "Cancelado", "percent": progress.get("percent", 0)})
            raise Exception("Cancelado")

        progress["percent"] = float(info.get("percent", 0))
        progress["message"] = info.get("status", "")

    downloader = VideoDownloader(output_dir=str(task_dir), progress_callback=progress_callback)
    download_tasks[task_id]["downloader"] = downloader

    try:
        progress.update({"status": "running", "message": "Iniciando", "percent": 0.0})

        if request.mode == "video":
            ok, message, _ = downloader.download_video(request.url, video_quality=request.video_quality)
            media_type = "mp4"
        else:
            ok, message, _ = downloader.download_audio(
                request.url,
                audio_format=request.audio_format,
                audio_quality=request.audio_quality,
            )
            media_type = request.audio_format

        if not ok:
            progress.update({"status": "error", "message": message, "percent": 0.0})
            return

        # Usa o arquivo mais recente como resultado
        files = sorted(task_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            progress.update({"status": "error", "message": "Arquivo não encontrado após download", "percent": 0.0})
            return

        result_file = files[0]
        progress.update({"status": "done", "message": "Download concluído", "percent": 100.0, "file": str(result_file), "media_type": media_type})

    except Exception as e:
        progress.update({"status": "error", "message": str(e), "percent": 0.0})


@app.post("/download")
def download_content(request: DownloadRequest):
    task_id = str(uuid.uuid4())
    download_progress[task_id] = {"status": "pending", "percent": 0.0, "message": "Aguardando"}
    download_tasks[task_id] = {"cancel_event": threading.Event(), "downloader": None}

    thread = threading.Thread(target=_run_download_task, args=(task_id, request), daemon=True)
    download_tasks[task_id]["thread"] = thread
    thread.start()

    return {"task_id": task_id}


@app.get("/download_progress/{task_id}")
def download_progress_status(task_id: str):
    if task_id not in download_progress:
        raise HTTPException(status_code=404, detail="Task ID não encontrado")
    return download_progress[task_id]


@app.get("/download_file/{task_id}")
def download_file(task_id: str):
    progress = download_progress.get(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task ID não encontrado")
    if progress.get("status") != "done":
        raise HTTPException(status_code=409, detail="Download ainda não concluído")

    file_path = progress.get("file")
    media_type = progress.get("media_type", "application/octet-stream")
    if not file_path:
        raise HTTPException(status_code=500, detail="Arquivo não encontrado")

    return FileResponse(path=str(file_path), filename=Path(file_path).name, media_type=f"{media_type}" if media_type else "application/octet-stream")

