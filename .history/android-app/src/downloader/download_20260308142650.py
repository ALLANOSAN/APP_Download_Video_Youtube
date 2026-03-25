# Faz o download do vídeo/áudio no formato escolhido
import yt_dlp
import os


def download_video(url, fmt, progress_callback=None):
    out_dir = os.path.expanduser("~/Download")

    def hook(d):
        if d["status"] == "downloading" and progress_callback:
            percent = (
                d.get("downloaded_bytes", 0) / max(1, d.get("total_bytes", 1)) * 100
                if d.get("total_bytes")
                else 0
            )
            progress_callback(percent)

    ydl_opts = {
        "format": fmt["format_id"],
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "progress_hooks": [hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
