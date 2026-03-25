"""
Módulo de configurações persistentes.
Salva preferências do usuário e histórico de downloads.
"""

import json
from pathlib import Path
from typing import Any


class Settings:
    """Gerencia configurações persistentes do aplicativo."""

    DEFAULT_SETTINGS = {
        "output_dir": "./downloads",
        "audio_format": "mp3",
        "audio_quality": "192k",
        "download_mode": "audio",  # "audio" ou "video"
        "video_quality": "720p",
        "history": [],  # Lista de URLs baixadas
        "max_history": 50,
    }

    def __init__(self, config_file: str | None = None):
        """Inicializa o gerenciador de configurações."""
        if config_file:
            self.config_path = Path(config_file)
        else:
            # Usa o diretório de configuração do usuário
            config_dir = Path.home() / ".config" / "youtube-downloader"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "settings.json"

        self._settings = self._load()

    def _load(self) -> dict[str, Any]:
        """Carrega configurações do arquivo."""
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    saved = json.load(f)
                    # Mescla com padrões para garantir que todas as chaves existam
                    return {**self.DEFAULT_SETTINGS, **saved}
            except (json.JSONDecodeError, OSError):
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()

    def _save(self) -> None:
        """Salva configurações no arquivo."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Erro ao salvar configurações: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém um valor de configuração."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Define um valor de configuração e salva."""
        self._settings[key] = value
        self._save()

    def add_to_history(self, url: str, title: str) -> None:
        """Adiciona uma URL ao histórico."""
        history = self._settings.get("history", [])

        # Remove duplicatas
        history = [h for h in history if h.get("url") != url]

        # Adiciona no início
        history.insert(0, {"url": url, "title": title})

        # Limita tamanho
        max_history = self._settings.get("max_history", 50)
        history = history[:max_history]

        self._settings["history"] = history
        self._save()

    def get_history(self) -> list[dict[str, str]]:
        """Retorna o histórico de downloads."""
        return self._settings.get("history", [])

    def clear_history(self) -> None:
        """Limpa o histórico de downloads."""
        self._settings["history"] = []
        self._save()

    @property
    def output_dir(self) -> str:
        return self.get("output_dir", "./downloads")

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        self.set("output_dir", value)

    @property
    def audio_format(self) -> str:
        return self.get("audio_format", "mp3")

    @audio_format.setter
    def audio_format(self, value: str) -> None:
        self.set("audio_format", value)

    @property
    def audio_quality(self) -> str:
        return self.get("audio_quality", "192k")

    @audio_quality.setter
    def audio_quality(self, value: str) -> None:
        self.set("audio_quality", value)

    @property
    def download_mode(self) -> str:
        return self.get("download_mode", "audio")

    @download_mode.setter
    def download_mode(self, value: str) -> None:
        self.set("download_mode", value)

    @property
    def video_quality(self) -> str:
        return self.get("video_quality", "720p")

    @video_quality.setter
    def video_quality(self, value: str) -> None:
        self.set("video_quality", value)


# Qualidades de áudio disponíveis
AUDIO_QUALITIES = ["128k", "192k", "256k", "320k"]

# Qualidades de vídeo disponíveis
VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "1440p", "4K"]

# Instância global
_settings: Settings | None = None


def get_settings() -> Settings:
    """Retorna a instância global de configurações."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
