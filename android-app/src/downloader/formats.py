# Lista formatos de áudio e vídeo disponíveis para um vídeo do YouTube
import yt_dlp


def get_formats(url):
    ydl_opts = {"quiet": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        for f in info.get("formats", []):
            if f.get("vcodec") == "none":
                # Áudio
                if f["ext"] in ["m4a", "mp3", "opus"]:
                    desc = f"{f.get('abr', '')}kbps"
                    formats.append(
                        {
                            "type": "Áudio",
                            "format": f["ext"],
                            "desc": desc,
                            "format_id": f["format_id"],
                        }
                    )
            else:
                # Vídeo
                if f["ext"] in ["mp4", "mkv"] and f.get("height") in [480, 720, 1080, 1440, 2160]:
                    desc = f"{f['height']}p"
                    formats.append(
                        {
                            "type": "Vídeo",
                            "format": f["ext"],
                            "desc": desc,
                            "format_id": f["format_id"],
                        }
                    )
        return formats
