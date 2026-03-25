# Suporte a download de playlists
import yt_dlp
import os

def download_playlist(url, fmt, progress_callback=None):
    out_dir = os.path.expanduser('~/Download')
    def hook(d):
        if progress_callback and d['status'] == 'downloading':
            progress_callback(d.get('downloaded_bytes', 0) / max(1, d.get('total_bytes', 1)))
    ydl_opts = {
        'format': fmt['format_id'],
        'outtmpl': os.path.join(out_dir, '%(playlist_title)s/%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': False,
        'progress_hooks': [hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
