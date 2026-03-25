import json
import os
import re
import stat
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

# Import relativo ou absoluto dependendo do contexto
try:
    from ..utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger  # ty: ignore[unresolved-import]


def resolve_binary(name: str, env_var: str) -> Path:
    """Localiza e marca executável do binário (yt-dlp/ffmpeg)."""
    candidates = []

    env_path = os.getenv(env_var)
    if env_path:
        candidates.append(Path(env_path))

    # Usa binários já empacotados no projeto (root/binaries)
    root = Path(__file__).resolve().parents[2]
    candidates.append(root / "binaries" / name)

    # Caminho relativo em src (quando se executa de mobile/main_flet.py)
    candidates.append(Path(__file__).resolve().parents[1] / "binaries" / name)

    # Caminho de trabalho atual
    candidates.append(Path.cwd() / "binaries" / name)

    # Caminhos do system PATH
    system_path = shutil.which(name)
    if system_path:
        candidates.append(Path(system_path))

    for candidate in candidates:
        if candidate and candidate.exists() and candidate.is_file():
            try:
                candidate.chmod(
                    candidate.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                )
            except Exception:
                pass
            return candidate

    raise FileNotFoundError(
        f"{name} não encontrado. Verifique se o binário está em 'binaries/', PATH ou variável de ambiente {env_var}."  # noqa: E501
    )


def get_base_path() -> Path:
    """Retorna o caminho base dos binários.

    Funciona tanto em desenvolvimento quanto quando empacotado com PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # Executando como executável (PyInstaller)
        return Path(sys._MEIPASS)  # type: ignore
    else:
        # Executando em desenvolvimento
        # Volta do src/downloader para a raiz do projeto
        return Path(__file__).parent.parent.parent


def get_binary_name(name: str) -> str:
    """Retorna o nome do binário com extensão correta para o SO."""
    if sys.platform == "win32":
        return f"{name}.exe"
    return name


# Formatos de áudio suportados
AUDIO_FORMATS = ["mp3", "m4a", "wav", "flac", "opus", "aac", "ogg"]

# Qualidades de áudio (bitrate)
AUDIO_QUALITIES = ["128k", "192k", "256k", "320k"]

# Qualidades de vídeo
VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "2160p"]


class VideoDownloader:
    def __init__(
        self,
        output_dir: str = "./downloads",
        progress_callback: Optional[Callable] = None,
    ):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self._stop_event = threading.Event()
        self.logger = get_logger()

        # Define caminhos dos binários de forma flexível
        self.ytdlp_path = resolve_binary(get_binary_name("yt-dlp"), "YT_DLP_PATH")
        self.ffmpeg_path = resolve_binary(get_binary_name("ffmpeg"), "FFMPEG_PATH")

        self.logger.info(f"VideoDownloader inicializado. Output: {self.output_dir}")

    def set_output_dir(self, output_dir: str) -> None:
        """Atualiza o diretório de saída."""
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_playlist_info(self, url: str) -> tuple[bool, str, Optional[list[dict]]]:
        """Obtém informações de uma playlist ou vídeo único.

        Returns:
            tuple[bool, str, Optional[list[dict]]]: (sucesso, mensagem, lista de vídeos)
        """
        try:
            self.logger.info(f"Buscando informações de: {url}")

            if not self.ytdlp_path.exists():
                self.logger.error(f"yt-dlp não encontrado: {self.ytdlp_path}")
                return False, f"yt-dlp não encontrado: {self.ytdlp_path}", None

            result = subprocess.run(
                [str(self.ytdlp_path), "--dump-json", "--flat-playlist", url],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Erro desconhecido"
                self.logger.error(f"Falha ao buscar informações: {error_msg}")
                return False, f"Falha ao buscar informações: {error_msg}", None

            # Cada linha é um JSON de um vídeo
            videos = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        info = json.loads(line)
                        video_id = info.get("id", "")
                        duration_raw = info.get("duration")
                        if duration_raw and isinstance(duration_raw, (int, float)):
                            minutes, seconds = divmod(int(duration_raw), 60)
                            hours, minutes = divmod(minutes, 60)
                            if hours > 0:
                                duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                            else:
                                duration = f"{minutes}:{seconds:02d}"
                        else:
                            duration = info.get("duration_string", "Unknown")

                        videos.append(
                            {
                                "id": video_id,
                                "title": info.get("title", "Unknown"),
                                "url": info.get(
                                    "url",
                                    info.get(
                                        "webpage_url",
                                        f"https://youtube.com/watch?v={video_id}",
                                    ),
                                ),
                                "duration": duration,
                                "uploader": info.get("uploader", info.get("channel", "Unknown")),
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            if videos:
                self.logger.info(f"Encontrado(s) {len(videos)} vídeo(s)")
                return True, f"Encontrado(s) {len(videos)} vídeo(s)", videos
            self.logger.warning("Nenhum vídeo encontrado")
            return False, "Nenhum vídeo encontrado", None

        except subprocess.TimeoutExpired:
            self.logger.error("Tempo limite excedido ao buscar informações")
            return False, "Tempo limite excedido ao buscar informações", None
        except Exception as e:
            self.logger.error(f"Erro ao buscar informações: {e}", exc_info=True)
            return False, f"Erro: {str(e)}", None

    def download_audio(
        self, url: str, audio_format: str = "m4a", audio_quality: str = "192k"
    ) -> tuple[bool, str, Optional[str]]:
        """Baixa áudio de um vídeo.

        Args:
            url: URL do vídeo
            audio_format: Formato de áudio (mp3, m4a, etc.)
            audio_quality: Qualidade/bitrate do áudio (128k, 192k, 320k)
        """
        if self._stop_event.is_set():
            return False, "Cancelado", None

        self.logger.info(f"Iniciando download de áudio: {url}")
        self.logger.info(f"Formato: {audio_format}, Qualidade: {audio_quality}")

        if not self.ytdlp_path.exists():
            self.logger.error(f"yt-dlp não encontrado: {self.ytdlp_path}")
            return False, f"yt-dlp não encontrado: {self.ytdlp_path}", None
        if not self.ffmpeg_path.exists():
            self.logger.error(f"ffmpeg não encontrado: {self.ffmpeg_path}")
            return False, f"ffmpeg não encontrado: {self.ffmpeg_path}", None

        output_template = self.output_dir / "%(title)s.%(ext)s"

        # Remove 'k' do bitrate se presente
        bitrate = audio_quality.replace("k", "")

        cmd = [
            str(self.ytdlp_path),
            "--no-playlist",
            "-x",
            "--audio-format",
            audio_format,
            "--audio-quality",
            bitrate,
            "--ffmpeg-location",
            str(self.ffmpeg_path.parent),
            "-o",
            str(output_template),
            url,
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            if process.stdout:
                for line in process.stdout:
                    if self._stop_event.is_set():
                        process.terminate()
                        return False, "Cancelado", None

                    if "%" in line:
                        try:
                            match = re.search(r"(\d+\.?\d*)%", line)
                            if match:
                                percent = float(match.group(1))
                                if self.progress_callback:
                                    self.progress_callback(
                                        {"percent": percent, "status": line.strip()}
                                    )
                        except ValueError:
                            pass

            return_code = process.wait()
            if return_code == 0:
                self.logger.info(f"Download de áudio concluído: {url}")
                return True, "Download concluído", str(self.output_dir)
            self.logger.error(f"Falha no download (código {return_code})")
            return False, f"Falha (código {return_code})", None
        except Exception as e:
            self.logger.error(f"Erro no download: {e}", exc_info=True)
            return False, str(e), None

    def download_video(
        self, url: str, audio_format: str = "m4a", video_quality: str = "720p"
    ) -> tuple[bool, str, Optional[str]]:
        """Baixa vídeo em MP4.

        Args:
            url: URL do vídeo
            audio_format: Ignorado para vídeo (mantido para compatibilidade)
            video_quality: Qualidade do vídeo (360p, 720p, 1080p etc. ou low/medium/high)
        """
        if self._stop_event.is_set():
            return False, "Cancelado", None

        self.logger.info(f"Iniciando download de vídeo: {url}")
        self.logger.info(f"Qualidade solicitada: {video_quality}")

        if not self.ytdlp_path.exists():
            self.logger.error(f"yt-dlp não encontrado: {self.ytdlp_path}")
            return False, f"yt-dlp não encontrado: {self.ytdlp_path}", None
        if not self.ffmpeg_path.exists():
            self.logger.error(f"ffmpeg não encontrado: {self.ffmpeg_path}")
            return False, f"ffmpeg não encontrado: {self.ffmpeg_path}", None

        output_template = self.output_dir / "%(title)s.%(ext)s"

        quality_map = {
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
            "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
        }

        alias_map = {"low": "360p", "medium": "720p", "high": "1080p"}
        requested_quality = alias_map.get(video_quality, video_quality)

        fallback_order = ["2160p", "1440p", "1080p", "720p", "480p", "360p"]
        if requested_quality in fallback_order:
            start_idx = fallback_order.index(requested_quality)
            candidates = [requested_quality] + fallback_order[start_idx + 1 :]
        else:
            candidates = [requested_quality] + fallback_order

        for quality_option in candidates:
            chosen_spec = quality_map.get(quality_option, "bestvideo+bestaudio/best")
            self.logger.info(f"Tentando qualidade: {quality_option} ({chosen_spec})")

            cmd = [
                str(self.ytdlp_path),
                "--no-playlist",
                "-f",
                chosen_spec,
                "--merge-output-format",
                "mp4",
                "--ffmpeg-location",
                str(self.ffmpeg_path.parent),
                "-o",
                str(output_template),
                url,
            ]

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                )

                if process.stdout:
                    for line in process.stdout:
                        if self._stop_event.is_set():
                            process.terminate()
                            return False, "Cancelado", None

                        if "%" in line:
                            try:
                                match = re.search(r"(\d+\.?\d*)%", line)
                                if match:
                                    percent = float(match.group(1))
                                    if self.progress_callback:
                                        self.progress_callback({"percent": percent, "status": line.strip()})
                            except ValueError:
                                pass

                return_code = process.wait()
                if return_code == 0:
                    self.logger.info(f"Download de vídeo concluído: {url} (qualidade {quality_option})")
                    return True, "Download concluído", str(self.output_dir)

                self.logger.warning(f"Falha no download de vídeo com qualidade {quality_option} (código {return_code})")

            except Exception as e:
                self.logger.error(f"Erro no download de vídeo com qualidade {quality_option}: {e}", exc_info=True)
                continue

        self.logger.error(f"Falha no download de vídeo para todas as qualidades solicitadas: {requested_quality}")
        return False, f"Falha (qualidade não disponível): {requested_quality}", None
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            if process.stdout:
                for line in process.stdout:
                    if self._stop_event.is_set():
                        process.terminate()
                        return False, "Cancelado", None

                    if "%" in line:
                        try:
                            match = re.search(r"(\d+\.?\d*)%", line)
                            if match:
                                percent = float(match.group(1))
                                if self.progress_callback:
                                    self.progress_callback(
                                        {"percent": percent, "status": line.strip()}
                                    )
                        except ValueError:
                            pass

            return_code = process.wait()
            if return_code == 0:
                self.logger.info(f"Download de vídeo concluído: {url}")
                return True, "Download concluído", str(self.output_dir)

            self.logger.warning(f"Falha no download de vídeo com qualidade {video_quality} (código {return_code}), tentando fallback...")

            # Fallback: tenta qualidade padrão best se não foi a escolhida
            if video_quality != "best":
                fallback_cmd = [
                    str(self.ytdlp_path),
                    "--no-playlist",
                    "-f",
                    "bestvideo+bestaudio/best",
                    "--merge-output-format",
                    "mp4",
                    "--ffmpeg-location",
                    str(self.ffmpeg_path.parent),
                    "-o",
                    str(output_template),
                    url,
                ]

                try:
                    fallback_process = subprocess.Popen(
                        fallback_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        bufsize=1,
                    )

                    if fallback_process.stdout:
                        for line in fallback_process.stdout:
                            if self._stop_event.is_set():
                                fallback_process.terminate()
                                return False, "Cancelado", None
                            if "%" in line:
                                try:
                                    match = re.search(r"(\d+\.?\d*)%", line)
                                    if match:
                                        percent = float(match.group(1))
                                        if self.progress_callback:
                                            self.progress_callback({"percent": percent, "status": line.strip()})
                                except ValueError:
                                    pass

                    fallback_return = fallback_process.wait()
                    if fallback_return == 0:
                        self.logger.info(f"Fallback de vídeo concluído: {url}")
                        return True, "Download concluído (fallback)", str(self.output_dir)
                    self.logger.error(f"Fallback também falhou (código {fallback_return})")
                    return False, f"Falha do download (nenhuma qualidade disponível)", None
                except Exception as ex:
                    self.logger.error(f"Erro no fallback de vídeo: {ex}", exc_info=True)
                    return False, str(ex), None

            self.logger.error(f"Falha no download de vídeo (código {return_code})")
            return False, f"Falha (código {return_code})", None
        except Exception as e:
            self.logger.error(f"Erro no download de vídeo: {e}", exc_info=True)
            return False, str(e), None

    def download_multiple(
        self,
        urls: list[str],
        audio_format: str = "m4a",
        audio_quality: str = "192k",
        download_mode: str = "audio",
        video_quality: str = "720p",
        item_callback: Optional[Callable] = None,
    ) -> tuple[int, int]:
        """Baixa múltiplos vídeos.

        Args:
            urls: Lista de URLs
            audio_format: Formato de áudio
            audio_quality: Qualidade/bitrate do áudio
            download_mode: "audio" ou "video"
            video_quality: Qualidade do vídeo (se modo vídeo)
            item_callback: Callback chamado para cada item (índice, total)

        Returns:
            tuple[int, int]: (sucesso, falhas)
        """
        success = 0
        failures = 0

        self.logger.info(f"Iniciando download de {len(urls)} itens")

        for i, url in enumerate(urls):
            if self._stop_event.is_set():
                break

            if item_callback:
                item_callback(i + 1, len(urls))

            if download_mode == "video":
                ok, msg, _ = self.download_video(url, video_quality=video_quality)
            else:
                ok, msg, _ = self.download_audio(url, audio_format, audio_quality)

            if ok:
                success += 1
            else:
                failures += 1
                self.logger.warning(f"Falha no item {i + 1}: {msg}")

        self.logger.info(f"Download concluído: {success} sucesso, {failures} falhas")
        return success, failures

    def get_video_info(self, url: str) -> tuple[bool, Optional[dict]]:
        """Obtém informações detalhadas do vídeo, incluindo thumbnail."""
        try:
            self.logger.debug(f"Obtendo informações de: {url}")

            if not self.ytdlp_path.exists():
                return False, None

            result = subprocess.run(
                [
                    str(self.ytdlp_path),
                    "--dump-json",
                    "--no-playlist",
                    "--skip-download",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                info = json.loads(result.stdout)

                # Obtém a melhor thumbnail disponível
                thumbnail = info.get("thumbnail", "")
                thumbnails = info.get("thumbnails", [])
                if thumbnails:
                    # Prefere thumbnail de maior qualidade
                    for t in reversed(thumbnails):
                        if t.get("url"):
                            thumbnail = t["url"]
                            break

                return True, {
                    "title": info.get("title", "Desconhecido"),
                    "duration": info.get("duration_string", "Desconhecido"),
                    "duration_seconds": info.get("duration", 0),
                    "uploader": info.get("uploader", "Desconhecido"),
                    "channel": info.get("channel", info.get("uploader", "Desconhecido")),
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "thumbnail": thumbnail,
                    "description": info.get("description", "")[:500],  # Limita descrição
                }
        except Exception as e:
            self.logger.error(f"Erro ao obter informações: {e}")
        return False, None

    def stop(self) -> None:
        """Para o download em andamento."""
        self._stop_event.set()

    def reset(self) -> None:
        """Reseta o estado para permitir novos downloads."""
        self._stop_event.clear()

    def search_youtube(
        self, query: str, max_results: int = 10
    ) -> tuple[bool, str, Optional[list[dict]]]:
        """Busca vídeos no YouTube usando yt-dlp (sem API).

        Args:
            query: Termo de busca
            max_results: Número máximo de resultados (padrão: 10)

        Returns:
            tuple[bool, str, Optional[list[dict]]]: (sucesso, mensagem, lista de vídeos)
        """
        try:
            self.logger.info(f"Buscando no YouTube: {query}")

            if not self.ytdlp_path.exists():
                return False, f"yt-dlp não encontrado: {self.ytdlp_path}", None

            # Usa ytsearch para buscar no YouTube
            search_query = f"ytsearch{max_results}:{query}"

            result = subprocess.run(
                [
                    str(self.ytdlp_path),
                    "--dump-json",
                    "--flat-playlist",
                    "--no-warnings",
                    search_query,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Erro na busca"
                self.logger.error(f"Falha na busca: {error_msg}")
                return False, f"Falha na busca: {error_msg}", None

            # Processa resultados
            videos = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        info = json.loads(line)
                        video_id = info.get("id", "")
                        if not video_id:
                            continue

                        duration_raw = info.get("duration")
                        if duration_raw and isinstance(duration_raw, (int, float)):
                            minutes, seconds = divmod(int(duration_raw), 60)
                            hours, minutes = divmod(minutes, 60)
                            if hours > 0:
                                duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                            else:
                                duration = f"{minutes}:{seconds:02d}"
                        else:
                            duration = info.get("duration_string", "?")

                        videos.append(
                            {
                                "id": video_id,
                                "title": info.get("title", "Sem título"),
                                "url": f"https://youtube.com/watch?v={video_id}",
                                "duration": duration,
                                "uploader": info.get("uploader", info.get("channel", "?")),
                                "view_count": info.get("view_count", 0),
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            if videos:
                self.logger.info(f"Busca retornou {len(videos)} resultados")
                return True, f"Encontrados {len(videos)} vídeos", videos

            return False, "Nenhum resultado encontrado", None

        except subprocess.TimeoutExpired:
            self.logger.error("Tempo limite excedido na busca")
            return False, "Tempo limite excedido", None
        except Exception as e:
            self.logger.error(f"Erro na busca: {e}", exc_info=True)
            return False, f"Erro: {str(e)}", None

    def download_subtitles(
        self, url: str, lang: str = "pt", auto_generated: bool = True
    ) -> tuple[bool, str, Optional[str]]:
        """Baixa legendas de um vídeo.

        Args:
            url: URL do vídeo
            lang: Código do idioma (pt, en, es, etc.)
            auto_generated: Se deve incluir legendas auto-geradas

        Returns:
            tuple[bool, str, Optional[str]]: (sucesso, mensagem, caminho do arquivo)
        """
        try:
            self.logger.info(f"Baixando legendas de: {url} (idioma: {lang})")

            if not self.ytdlp_path.exists():
                return False, "yt-dlp não encontrado", None

            output_template = self.output_dir / "%(title)s.%(ext)s"

            cmd = [
                str(self.ytdlp_path),
                "--skip-download",
                "--write-sub",
                "--sub-lang",
                lang,
                "--sub-format",
                "srt/best",
                "--convert-subs",
                "srt",
                "-o",
                str(output_template),
                url,
            ]

            # Adiciona legendas auto-geradas se solicitado
            if auto_generated:
                cmd.insert(3, "--write-auto-sub")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                self.logger.info("Legendas baixadas com sucesso")
                return True, "Legendas baixadas", str(self.output_dir)

            # Verifica se não há legendas disponíveis
            if "no subtitles" in result.stderr.lower():
                return False, f"Nenhuma legenda disponível em '{lang}'", None

            error_msg = result.stderr.strip() if result.stderr else "Erro desconhecido"
            return False, f"Falha: {error_msg}", None

        except subprocess.TimeoutExpired:
            return False, "Tempo limite excedido", None
        except Exception as e:
            self.logger.error(f"Erro ao baixar legendas: {e}")
            return False, f"Erro: {str(e)}", None

    def get_available_subtitles(self, url: str) -> tuple[bool, Optional[list[dict]]]:
        """Lista legendas disponíveis para um vídeo.

        Returns:
            tuple[bool, Optional[list[dict]]]: (sucesso, lista de legendas)
        """
        try:
            if not self.ytdlp_path.exists():
                return False, None

            result = subprocess.run(
                [
                    str(self.ytdlp_path),
                    "--list-subs",
                    "--no-warnings",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            subtitles = []
            lines = result.stdout.split("\n")

            # Parse das legendas disponíveis
            in_subs_section = False
            for line in lines:
                if "Available subtitles" in line or "Available automatic captions" in line:
                    in_subs_section = True
                    continue
                if in_subs_section and line.strip():
                    # Formato: "pt       vtt, ..."
                    parts = line.split()
                    if parts and len(parts[0]) <= 5:  # Código de idioma
                        lang_code = parts[0]
                        is_auto = "automatic" in line.lower()
                        subtitles.append(
                            {
                                "code": lang_code,
                                "auto_generated": is_auto,
                            }
                        )

            return True, subtitles if subtitles else None

        except Exception as e:
            self.logger.error(f"Erro ao listar legendas: {e}")
            return False, None
