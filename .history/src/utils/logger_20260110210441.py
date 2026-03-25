"""
Módulo de logging para o aplicativo.
Salva logs de erro e informações em arquivo.
"""

import logging
from datetime import datetime
from pathlib import Path


class AppLogger:
    """Logger configurável para o aplicativo."""

    def __init__(self, name: str = "youtube-downloader", log_dir: str | None = None):
        """Inicializa o logger."""
        self.name = name

        # Define diretório de logs
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".config" / "youtube-downloader" / "logs"

        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Arquivo de log do dia atual
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"{today}.log"

        # Configura o logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove handlers existentes
        self.logger.handlers.clear()

        # Handler para arquivo
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Handler para console (apenas warnings e erros)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Formato do log
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str) -> None:
        """Log de debug."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Log de informação."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log de aviso."""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log de erro."""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """Log crítico."""
        self.logger.critical(message, exc_info=exc_info)

    def get_log_file(self) -> Path:
        """Retorna o caminho do arquivo de log atual."""
        return self.log_file

    def get_recent_logs(self, lines: int = 100) -> str:
        """Retorna as últimas linhas do log."""
        if not self.log_file.exists():
            return "Nenhum log encontrado."

        try:
            with open(self.log_file, encoding="utf-8") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except OSError:
            return "Erro ao ler arquivo de log."

    def clear_old_logs(self, days: int = 30) -> int:
        """Remove logs mais antigos que X dias. Retorna quantidade removida."""
        removed = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff:
                try:
                    log_file.unlink()
                    removed += 1
                except OSError:
                    pass

        return removed


# Instância global
_logger: AppLogger | None = None


def get_logger() -> AppLogger:
    """Retorna a instância global do logger."""
    global _logger
    if _logger is None:
        _logger = AppLogger()
    return _logger
