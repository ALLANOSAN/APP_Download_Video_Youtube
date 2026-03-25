# Busca vídeos no YouTube sem API oficial usando yt-dlp
import yt_dlp


def search_youtube(query):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": "ytsearch10",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(query, download=False)
        entries = result["entries"] if "entries" in result else []
        return [
            {"title": e.get("title", ""), "url": f"https://www.youtube.com/watch?v={e['id']}"}
            for e in entries
            if e.get("id")
        ]
