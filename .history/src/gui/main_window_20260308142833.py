"""
Interface gráfica principal do YouTube Downloader.
Usa PySide6 para uma UI moderna com tema escuro.
"""

import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QAbstractItemView,
    QListWidget,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap


try:
    from ..downloader.video_downloader import (
        VideoDownloader,
        AUDIO_FORMATS,
        AUDIO_QUALITIES,
        VIDEO_QUALITIES,
    )
    from ..utils.settings import get_settings
    from ..utils.logger import get_logger
except ImportError:
    from downloader.video_downloader import (  # ty: ignore[unresolved-import]
        VideoDownloader,
        AUDIO_FORMATS,
        AUDIO_QUALITIES,
        VIDEO_QUALITIES,
    )
    from utils.settings import get_settings  # ty: ignore[unresolved-import]
    from utils.logger import get_logger  # ty: ignore[unresolved-import]


class WorkerThread(QThread):
    """Thread para executar operações em background."""

    finished = Signal(bool, str, object)
    progress = Signal(dict)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            if isinstance(result, tuple):
                self.finished.emit(
                    result[0],
                    str(result[1]) if len(result) > 1 else "",
                    result[2] if len(result) > 2 else None,
                )
            else:
                self.finished.emit(True, "", result)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class ThumbnailLabel(QLabel):
    """Label que carrega thumbnails assincronamente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 90)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #2a2a4a;
                border-radius: 5px;
                border: 1px solid #4a4a6a;
            }
        """)
        self.setText("📷")
        self._thumb_thread: Optional[QThread] = None

    def load_thumbnail(self, url: str):
        """Carrega thumbnail de uma URL."""
        if not url:
            self.setText("📷")
            return

        try:
            # Baixa a imagem em background
            thread = ThumbnailThread(url)
            thread.finished.connect(self._on_thumbnail_loaded)
            thread.start()
            self._thumb_thread = thread  # Mantém referência
        except Exception:
            self.setText("📷")

    def _on_thumbnail_loaded(self, data: bytes):
        """Callback quando a thumbnail é carregada."""
        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            scaled = pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
        else:
            self.setText("📷")


class ThumbnailThread(QThread):
    """Thread para carregar thumbnail."""

    finished = Signal(bytes)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            with urllib.request.urlopen(self.url, timeout=10) as response:
                self.finished.emit(response.read())
        except Exception:
            self.finished.emit(b"")


class PlaylistDialog(QWidget):
    """Janela para seleção de itens da playlist."""

    download_requested = Signal(list)

    def __init__(self, videos: list[dict], parent=None):
        super().__init__(parent)
        self.videos = videos
        self.setWindowTitle("Selecionar Músicas da Playlist")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel(f"📋 Playlist com {len(self.videos)} músicas")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["", "Título", "Duração", "Canal"])
        self.table.setRowCount(len(self.videos))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 180)

        for i, video in enumerate(self.videos):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.table.setCellWidget(i, 0, checkbox)

            # Título
            title_item = QTableWidgetItem(video.get("title", "Desconhecido"))
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 1, title_item)

            # Duração
            duration = video.get("duration", "?")
            if isinstance(duration, (int, float)):
                mins, secs = divmod(int(duration), 60)
                duration = f"{mins}:{secs:02d}"
            duration_item = QTableWidgetItem(str(duration))
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 2, duration_item)

            # Uploader
            uploader_item = QTableWidgetItem(video.get("uploader", "Desconhecido"))
            uploader_item.setFlags(uploader_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 3, uploader_item)

        layout.addWidget(self.table)

        # Botões de seleção
        select_layout = QHBoxLayout()

        select_all_btn = QPushButton("✓ Selecionar Todos")
        select_all_btn.clicked.connect(self._select_all)
        select_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("✗ Desmarcar Todos")
        deselect_all_btn.clicked.connect(self._deselect_all)
        select_layout.addWidget(deselect_all_btn)

        select_layout.addStretch()

        self.selected_label = QLabel(f"{len(self.videos)} selecionadas")
        select_layout.addWidget(self.selected_label)

        layout.addLayout(select_layout)

        # Botões de ação
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)

        download_btn = QPushButton("⬇ Baixar Selecionadas")
        download_btn.setMinimumHeight(40)
        download_btn.setObjectName("greenButton")
        download_btn.clicked.connect(self._download_selected)
        btn_layout.addWidget(download_btn)

        layout.addLayout(btn_layout)

        # Conectar checkboxes para atualizar contador
        for i in range(len(self.videos)):
            checkbox = self.table.cellWidget(i, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.stateChanged.connect(self._update_count)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #eee;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTableWidget {
                background-color: #16213e;
                border: 1px solid #4a4a6a;
                gridline-color: #4a4a6a;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #0f3460;
                padding: 8px;
                border: 1px solid #4a4a6a;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                background-color: #e94560;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton#greenButton {
                background-color: #4CAF50;
            }
            QPushButton#greenButton:hover {
                background-color: #45a049;
            }
        """)

    def _select_all(self):
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

    def _deselect_all(self):
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)

    def _update_count(self):
        count = 0
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                count += 1
        self.selected_label.setText(f"{count} selecionadas")

    def _download_selected(self):
        selected_urls = []
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                video_id = self.videos[i].get("id", "")
                url = self.videos[i].get("url", f"https://youtube.com/watch?v={video_id}")
                if not url.startswith("http"):
                    url = f"https://youtube.com/watch?v={video_id}"
                selected_urls.append(url)

        if selected_urls:
            self.download_requested.emit(selected_urls)
            self.close()
        else:
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos uma música!")


class SearchDialog(QWidget):
    """Janela de busca no YouTube."""

    video_selected = Signal(str, str)  # url, title

    def __init__(self, downloader, parent=None):
        super().__init__(parent)
        self.downloader = downloader
        self.setWindowTitle("🔍 Buscar no YouTube")
        self.setMinimumSize(700, 500)
        self.setWindowFlags(Qt.WindowType.Window)
        self._current_query = ""
        self._current_page = 0
        self._page_size = 30
        self._initial_load = 50  # Primeira busca carrega mais
        self._max_results = 100  # Limite do yt-dlp ytsearch
        self._is_loading = False
        self._has_more = True
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Campo de busca
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o que deseja buscar...")
        self.search_input.returnPressed.connect(self._do_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍 Buscar")
        self.search_btn.clicked.connect(self._do_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Status
        self.status_label = QLabel("Digite um termo e clique em Buscar")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # Tabela de resultados
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Título", "Canal", "Duração", "Views"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 80)
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.verticalScrollBar().valueChanged.connect(self._on_scroll)
        layout.addWidget(self.table)

        # Botão carregar mais
        self.load_more_btn = QPushButton("📥 Carregar Mais Resultados")
        self.load_more_btn.clicked.connect(self._load_more_results)
        self.load_more_btn.setVisible(False)
        layout.addWidget(self.load_more_btn)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        select_btn = QPushButton("✓ Selecionar")
        select_btn.clicked.connect(self._select_video)
        btn_layout.addWidget(select_btn)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self._results: list[dict] = []

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #eee;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #4a4a6a;
                border-radius: 5px;
                background-color: #0f3460;
                color: white;
            }
            QTableWidget {
                background-color: #16213e;
                border: 1px solid #4a4a6a;
                gridline-color: #4a4a6a;
            }
            QHeaderView::section {
                background-color: #0f3460;
                padding: 8px;
                border: 1px solid #4a4a6a;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                background-color: #e94560;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
        """)

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        # Nova busca - resetar estado
        self._current_query = query
        self._current_page = 0
        self._has_more = True
        self._results = []
        self.table.setRowCount(0)

        self._load_more_results()

    def _on_scroll(self):
        """Detecta quando usuário chega perto do fim da lista."""
        if self._is_loading or not self._has_more:
            return

        scrollbar = self.table.verticalScrollBar()
        max_val = scrollbar.maximum()

        # Se não há scroll (poucos itens), não faz nada
        if max_val == 0:
            return

        # Carrega mais quando estiver a 70% do scroll
        if scrollbar.value() >= max_val * 0.7:
            self._load_more_results()

    def _load_more_results(self):
        """Carrega mais resultados."""
        if self._is_loading or not self._current_query:
            return

        self._is_loading = True
        self.status_label.setText("🔄 Buscando...")
        self.search_btn.setEnabled(False)

        # Calcula quantos resultados buscar
        current_count = len(self._results)

        if current_count >= self._max_results:
            self._has_more = False
            self._is_loading = False
            self.search_btn.setEnabled(True)
            self.status_label.setText(f"✓ {current_count} resultados (máximo atingido)")
            return

        # Primeira busca carrega mais, depois incrementa
        if current_count == 0:
            total_to_fetch = self._initial_load
        else:
            total_to_fetch = min(current_count + self._page_size, self._max_results)

        # Executa busca em thread
        self.worker = WorkerThread(
            self.downloader.search_youtube, self._current_query, total_to_fetch
        )
        self.worker.finished.connect(self._on_search_finished)
        self.worker.start()

    def _on_search_finished(self, success: bool, message: str, data):
        self.search_btn.setEnabled(True)
        self._is_loading = False

        if success and data:
            # Filtra apenas os novos resultados (que ainda não temos)
            existing_ids = {v["id"] for v in self._results}
            new_videos = [v for v in data if v["id"] not in existing_ids]

            if not new_videos:
                self._has_more = False
                self.status_label.setText(f"✓ {len(self._results)} resultados (todos carregados)")
                return

            # Adiciona novos vídeos
            start_row = len(self._results)
            self._results.extend(new_videos)
            self.table.setRowCount(len(self._results))

            for i, video in enumerate(new_videos):
                row = start_row + i
                # Título
                title_item = QTableWidgetItem(video.get("title", "?"))
                title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, title_item)

                # Canal
                channel_item = QTableWidgetItem(video.get("uploader", "?"))
                channel_item.setFlags(channel_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, channel_item)

                # Duração
                dur_item = QTableWidgetItem(str(video.get("duration", "?")))
                dur_item.setFlags(dur_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, dur_item)

                # Views
                views = video.get("view_count", 0)
                if views >= 1_000_000:
                    views_str = f"{views / 1_000_000:.1f}M"
                elif views >= 1_000:
                    views_str = f"{views / 1_000:.0f}K"
                else:
                    views_str = str(views) if views else "?"
                views_item = QTableWidgetItem(views_str)
                views_item.setFlags(views_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 3, views_item)

            self._current_page += 1

            # Verifica se ainda há mais
            if len(self._results) >= self._max_results or len(new_videos) < self._page_size:
                self._has_more = False
                self.load_more_btn.setVisible(False)
                self.status_label.setText(f"✓ {len(self._results)} resultados (todos carregados)")
            else:
                self._has_more = True
                self.load_more_btn.setVisible(True)
                self.status_label.setText(
                    f"✓ {len(self._results)} resultados (clique em 'Carregar Mais' ou role)"
                )
        else:
            if len(self._results) > 0:
                self._has_more = False
                self.load_more_btn.setVisible(False)
                self.status_label.setText(f"✓ {len(self._results)} resultados (todos carregados)")
            else:
                self.load_more_btn.setVisible(False)
                self.status_label.setText(f"❌ {message}")

    def _on_double_click(self):
        self._select_video()

    def _select_video(self):
        row = self.table.currentRow()
        if row >= 0 and row < len(self._results):
            video = self._results[row]
            self.video_selected.emit(video["url"], video["title"])
            self.close()


class DownloadQueueDialog(QWidget):
    """Janela de fila de downloads."""

    start_downloads = Signal(list)  # Lista de URLs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 Fila de Downloads")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(Qt.WindowType.Window)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Instruções
        info = QLabel("Adicione URLs uma por linha ou cole múltiplas URLs:")
        layout.addWidget(info)

        # Campo de texto para adicionar
        add_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole uma URL e pressione Enter ou clique em Adicionar")
        self.url_input.returnPressed.connect(self._add_url)
        add_layout.addWidget(self.url_input)

        add_btn = QPushButton("➕ Adicionar")
        add_btn.clicked.connect(self._add_url)
        add_layout.addWidget(add_btn)

        layout.addLayout(add_layout)

        # Lista de URLs
        self.url_list = QListWidget()
        self.url_list.setAlternatingRowColors(True)
        layout.addWidget(self.url_list)

        # Contador
        self.count_label = QLabel("0 URLs na fila")
        self.count_label.setStyleSheet("color: #888;")
        layout.addWidget(self.count_label)

        # Botões
        btn_layout = QHBoxLayout()

        paste_btn = QPushButton("📋 Colar da Área de Transferência")
        paste_btn.clicked.connect(self._paste_from_clipboard)
        btn_layout.addWidget(paste_btn)

        clear_btn = QPushButton("🗑 Limpar")
        clear_btn.clicked.connect(self._clear_list)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()

        start_btn = QPushButton("⬇ Iniciar Downloads")
        start_btn.setObjectName("greenButton")
        start_btn.clicked.connect(self._start_downloads)
        btn_layout.addWidget(start_btn)

        layout.addLayout(btn_layout)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #eee;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #4a4a6a;
                border-radius: 5px;
                background-color: #0f3460;
                color: white;
            }
            QListWidget {
                background-color: #16213e;
                border: 1px solid #4a4a6a;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #4a4a6a;
            }
            QListWidget::item:selected {
                background-color: #e94560;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
                background-color: #e94560;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton#greenButton {
                background-color: #4CAF50;
            }
            QPushButton#greenButton:hover {
                background-color: #45a049;
            }
        """)

    def _add_url(self):
        url = self.url_input.text().strip()
        if url and self._is_valid_url(url):
            self.url_list.addItem(url)
            self.url_input.clear()
            self._update_count()
        elif url:
            QMessageBox.warning(self, "Aviso", "URL inválida!")

    def _paste_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if text:
            # Divide por linhas
            lines = text.strip().split("\n")
            added = 0
            for line in lines:
                url = line.strip()
                if url and self._is_valid_url(url):
                    self.url_list.addItem(url)
                    added += 1

            self._update_count()
            if added > 0:
                QMessageBox.information(self, "Sucesso", f"{added} URLs adicionadas!")

    def _clear_list(self):
        self.url_list.clear()
        self._update_count()

    def _update_count(self):
        count = self.url_list.count()
        self.count_label.setText(f"{count} URLs na fila")

    def _is_valid_url(self, url: str) -> bool:
        patterns = [
            "youtube.com/watch",
            "youtu.be/",
            "youtube.com/shorts/",
            "music.youtube.com/",
        ]
        return any(p in url for p in patterns)

    def _start_downloads(self):
        urls = []
        for i in range(self.url_list.count()):
            urls.append(self.url_list.item(i).text())

        if urls:
            self.start_downloads.emit(urls)
            self.close()
        else:
            QMessageBox.warning(self, "Aviso", "Adicione pelo menos uma URL!")


class YouTubeDownloaderApp(QMainWindow):
    """Janela principal do aplicativo."""

    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.logger = get_logger()
        self.downloader = VideoDownloader(
            output_dir=self.settings.output_dir,
            progress_callback=self._on_progress,
        )
        self.is_downloading = False
        self.worker: Optional[WorkerThread] = None
        self.playlist_dialog: Optional[PlaylistDialog] = None
        self.search_dialog: Optional[SearchDialog] = None
        self.queue_dialog: Optional[DownloadQueueDialog] = None
        self._playlist_videos: Optional[list[dict]] = None
        self._current_video_info: Optional[dict] = None

        # Variáveis para download múltiplo
        self._download_queue: list[str] = []
        self._download_index = 0
        self._download_success = 0
        self._download_failures = 0
        self._audio_format = "mp3"
        self._audio_quality = "192k"
        self._is_audio_mode = True

        # Variáveis para legendas
        self._download_subs = False
        self._sub_lang = "pt"
        self._auto_subs = True

        self._setup_ui()
        self._load_settings()

        self.logger.info("Aplicativo iniciado")

    def _setup_ui(self):
        self.setWindowTitle("🎵 YouTube Downloader Pro")
        self.setMinimumSize(700, 700)
        self._apply_style()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("🎵 YouTube Downloader Pro")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #e94560; margin-bottom: 10px;")
        layout.addWidget(title)

        # URL Input com Histórico
        url_group = QGroupBox("URL do Vídeo ou Playlist")
        url_layout = QVBoxLayout(url_group)

        # Combo de histórico
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Histórico:"))
        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(300)
        self.history_combo.currentIndexChanged.connect(self._on_history_selected)
        history_layout.addWidget(self.history_combo)

        clear_history_btn = QPushButton("🗑")
        clear_history_btn.setFixedWidth(35)
        clear_history_btn.setToolTip("Limpar histórico")
        clear_history_btn.clicked.connect(self._clear_history)
        history_layout.addWidget(clear_history_btn)
        history_layout.addStretch()
        url_layout.addLayout(history_layout)

        # Input de URL
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole aqui a URL do YouTube...")
        self.url_input.returnPressed.connect(self._fetch_info)
        url_input_layout.addWidget(self.url_input)

        self.fetch_btn = QPushButton("🔍 Buscar")
        self.fetch_btn.setMinimumWidth(100)
        self.fetch_btn.clicked.connect(self._fetch_info)
        url_input_layout.addWidget(self.fetch_btn)

        url_layout.addLayout(url_input_layout)

        # Botões extras: Busca YouTube e Fila
        extra_btn_layout = QHBoxLayout()

        search_yt_btn = QPushButton("🔎 Buscar no YouTube")
        search_yt_btn.setToolTip("Pesquisar vídeos no YouTube")
        search_yt_btn.clicked.connect(self._open_search_dialog)
        extra_btn_layout.addWidget(search_yt_btn)

        queue_btn = QPushButton("📋 Fila de Downloads")
        queue_btn.setToolTip("Adicionar múltiplas URLs para download")
        queue_btn.clicked.connect(self._open_queue_dialog)
        extra_btn_layout.addWidget(queue_btn)

        extra_btn_layout.addStretch()
        url_layout.addLayout(extra_btn_layout)

        layout.addWidget(url_group)

        # Info com Thumbnail
        info_group = QGroupBox("Informações")
        info_layout = QHBoxLayout(info_group)

        # Thumbnail
        self.thumbnail_label = ThumbnailLabel()
        info_layout.addWidget(self.thumbnail_label)

        # Texto de informações
        self.info_label = QLabel("Aguardando URL...")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("padding: 10px;")
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        self.info_label.setMinimumHeight(90)
        info_layout.addWidget(self.info_label, 1)

        layout.addWidget(info_group)

        # Opções
        options_group = QGroupBox("Opções de Download")
        options_layout = QVBoxLayout(options_group)

        # Linha 1: Modo e Qualidade
        mode_layout = QHBoxLayout()

        mode_layout.addWidget(QLabel("Modo:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["🎵 Áudio", "🎬 Vídeo"])
        self.mode_combo.setMinimumWidth(120)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        mode_layout.addSpacing(20)

        self.format_label = QLabel("Formato:")
        mode_layout.addWidget(self.format_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(AUDIO_FORMATS)
        self.format_combo.setMinimumWidth(80)
        mode_layout.addWidget(self.format_combo)

        mode_layout.addSpacing(20)

        self.quality_label = QLabel("Qualidade:")
        mode_layout.addWidget(self.quality_label)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(AUDIO_QUALITIES)
        self.quality_combo.setMinimumWidth(80)
        mode_layout.addWidget(self.quality_combo)

        mode_layout.addStretch()
        options_layout.addLayout(mode_layout)

        # Linha 1.5: Opção de legendas
        subtitle_layout = QHBoxLayout()

        self.subtitle_checkbox = QCheckBox("📝 Baixar legendas")
        self.subtitle_checkbox.setToolTip("Baixa legendas em .srt junto com o vídeo/áudio")
        subtitle_layout.addWidget(self.subtitle_checkbox)

        subtitle_layout.addWidget(QLabel("Idioma:"))
        self.subtitle_lang = QComboBox()
        self.subtitle_lang.addItems(["pt", "en", "es", "fr", "de", "it", "ja", "ko", "zh"])
        self.subtitle_lang.setToolTip("Idioma preferido das legendas")
        self.subtitle_lang.setMinimumWidth(60)
        subtitle_layout.addWidget(self.subtitle_lang)

        self.auto_sub_checkbox = QCheckBox("Incluir auto-geradas")
        self.auto_sub_checkbox.setChecked(True)
        self.auto_sub_checkbox.setToolTip("Inclui legendas geradas automaticamente pelo YouTube")
        subtitle_layout.addWidget(self.auto_sub_checkbox)

        subtitle_layout.addStretch()
        options_layout.addLayout(subtitle_layout)

        # Linha 2: Diretório
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Salvar em:"))
        self.dir_input = QLineEdit()
        self.dir_input.setText(str(self.downloader.output_dir))
        dir_layout.addWidget(self.dir_input)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(35)
        browse_btn.setToolTip("Procurar pasta")
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout.addWidget(browse_btn)

        open_folder_btn = QPushButton("📂 Abrir")
        open_folder_btn.setToolTip("Abrir pasta de downloads")
        open_folder_btn.clicked.connect(self._open_download_folder)
        dir_layout.addWidget(open_folder_btn)

        options_layout.addLayout(dir_layout)
        layout.addWidget(options_group)

        # Progresso
        progress_group = QGroupBox("Progresso")
        progress_layout = QVBoxLayout(progress_group)

        # Barra principal
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)

        # Label de status
        self.progress_label = QLabel("Pronto")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        # Label de item atual (para playlists)
        self.item_label = QLabel("")
        self.item_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.item_label.setStyleSheet("color: #888; font-size: 11px;")
        progress_layout.addWidget(self.item_label)

        layout.addWidget(progress_group)

        # Botões de ação
        btn_layout = QHBoxLayout()

        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.setMinimumHeight(50)
        self.download_btn.setObjectName("greenButton")
        self.download_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self.download_btn)

        self.stop_btn = QPushButton("⏹ Parar")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_download)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        # Botão de logs
        logs_layout = QHBoxLayout()
        logs_layout.addStretch()

        logs_btn = QPushButton("📋 Ver Logs")
        logs_btn.setMinimumWidth(100)
        logs_btn.clicked.connect(self._show_logs)
        logs_layout.addWidget(logs_btn)

        layout.addLayout(logs_layout)

        # Status bar
        self.statusBar().showMessage("Pronto para baixar")

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                color: #eee;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a4a6a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #16213e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 2px solid #4a4a6a;
                border-radius: 5px;
                background-color: #0f3460;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #e94560;
            }
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                background-color: #e94560;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:disabled {
                background-color: #4a4a6a;
                color: #888;
            }
            QPushButton#greenButton {
                background-color: #4CAF50;
                font-size: 15px;
            }
            QPushButton#greenButton:hover {
                background-color: #45a049;
            }
            QPushButton#greenButton:disabled {
                background-color: #4a4a6a;
            }
            QProgressBar {
                border: 2px solid #4a4a6a;
                border-radius: 5px;
                text-align: center;
                background-color: #0f3460;
            }
            QProgressBar::chunk {
                background-color: #e94560;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #0f3460;
                selection-background-color: #e94560;
            }
            QStatusBar {
                background-color: #16213e;
                color: #888;
            }
        """)

    def _load_settings(self):
        """Carrega configurações salvas."""
        # Diretório
        self.dir_input.setText(self.settings.output_dir)
        self.downloader.set_output_dir(self.settings.output_dir)

        # Formato
        audio_format = self.settings.audio_format
        idx = self.format_combo.findText(audio_format)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)

        # Qualidade
        audio_quality = self.settings.audio_quality
        idx = self.quality_combo.findText(audio_quality)
        if idx >= 0:
            self.quality_combo.setCurrentIndex(idx)

        # Modo
        download_mode = self.settings.download_mode
        self.mode_combo.setCurrentIndex(0 if download_mode == "audio" else 1)
        self._on_mode_changed()

        # Histórico
        self._update_history_combo()

    def _save_settings(self):
        """Salva configurações atuais."""
        self.settings.output_dir = self.dir_input.text()
        self.settings.audio_format = self.format_combo.currentText()
        self.settings.audio_quality = self.quality_combo.currentText()
        mode = "audio" if self.mode_combo.currentIndex() == 0 else "video"
        self.settings.download_mode = mode
        if mode == "video":
            self.settings.video_quality = self.quality_combo.currentText()

    def _update_history_combo(self):
        """Atualiza o combo de histórico."""
        self.history_combo.clear()
        self.history_combo.addItem("-- Selecione do histórico --")
        for item in self.settings.get_history():
            title = item.get("title", "")[:50]
            if len(item.get("title", "")) > 50:
                title += "..."
            self.history_combo.addItem(title, item.get("url"))

    def _on_history_selected(self, index: int):
        """Quando um item do histórico é selecionado."""
        if index > 0:
            url = self.history_combo.itemData(index)
            if url:
                self.url_input.setText(url)
                self._fetch_info()

    def _clear_history(self):
        """Limpa o histórico."""
        reply = QMessageBox.question(
            self,
            "Limpar Histórico",
            "Deseja limpar todo o histórico de downloads?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear_history()
            self._update_history_combo()
            self.logger.info("Histórico limpo")

    def _on_mode_changed(self):
        """Quando o modo de download muda."""
        is_audio = self.mode_combo.currentIndex() == 0

        if is_audio:
            self.format_label.setText("Formato:")
            self.format_combo.clear()
            self.format_combo.addItems(AUDIO_FORMATS)
            self.quality_label.setText("Bitrate:")
            self.quality_combo.clear()
            self.quality_combo.addItems(AUDIO_QUALITIES)
        else:
            self.format_label.setText("Container:")
            self.format_combo.clear()
            self.format_combo.addItem("mp4")
            self.quality_label.setText("Resolução:")
            self.quality_combo.clear()
            self.quality_combo.addItems(VIDEO_QUALITIES)

    def _browse_dir(self):
        """Abre diálogo para selecionar diretório."""
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if directory:
            self.dir_input.setText(directory)
            self._save_settings()

    def _open_download_folder(self):
        """Abre a pasta de downloads no gerenciador de arquivos."""
        folder = Path(self.dir_input.text())
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)

        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", str(folder)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)])
            else:
                subprocess.run(["xdg-open", str(folder)])
            self.logger.info(f"Pasta aberta: {folder}")
        except Exception as e:
            self.logger.error(f"Erro ao abrir pasta: {e}")
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir a pasta: {e}")

    def _fetch_info(self):
        """Busca informações do vídeo/playlist."""
        url = self.url_input.text().strip()
        if not url:
            return

        if not self._is_valid_youtube_url(url):
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL válida do YouTube!")
            return

        self.info_label.setText("🔄 Buscando informações...")
        self.thumbnail_label.setText("⏳")
        self.fetch_btn.setEnabled(False)
        self.statusBar().showMessage("Buscando informações...")

        self.worker = WorkerThread(self.downloader.get_playlist_info, url)
        self.worker.finished.connect(self._on_fetch_finished)
        self.worker.start()

    def _on_fetch_finished(self, success: bool, message: str, data):
        """Callback quando a busca termina."""
        self.fetch_btn.setEnabled(True)

        if success and data:
            videos = data
            if len(videos) == 1:
                # Vídeo único - busca info detalhada
                self._playlist_videos = None
                video = videos[0]
                url = self.url_input.text().strip()
                self._fetch_detailed_info(url, video)
            else:
                # Playlist
                self.info_label.setText(
                    f"📋 <b>Playlist encontrada!</b><br>"
                    f"🎵 {len(videos)} músicas disponíveis<br>"
                    f"Clique em Download para selecionar as músicas"
                )
                self.thumbnail_label.setText("📋")
                self.statusBar().showMessage(f"Playlist com {len(videos)} músicas")
                self._playlist_videos = videos
                self._current_video_info = None
        else:
            error_msg = message if message else "Erro desconhecido"
            self.info_label.setText(f"❌ {error_msg}")
            self.thumbnail_label.setText("❌")
            self.statusBar().showMessage("Erro ao buscar informações")
            self._playlist_videos = None
            self._current_video_info = None

    def _fetch_detailed_info(self, url: str, basic_info: dict):
        """Busca informações detalhadas de um vídeo único."""
        self.worker = WorkerThread(self.downloader.get_video_info, url)
        self.worker.finished.connect(
            lambda ok, msg, data: self._on_detailed_info(ok, msg, data, basic_info)
        )
        self.worker.start()

    def _on_detailed_info(
        self, success: bool, message: str, data: Optional[dict], basic_info: dict
    ):
        """Callback com informações detalhadas."""
        if success and data:
            self._current_video_info = data

            # Formata views
            views = data.get("view_count", 0)
            if views >= 1_000_000:
                views_str = f"{views / 1_000_000:.1f}M"
            elif views >= 1_000:
                views_str = f"{views / 1_000:.1f}K"
            else:
                views_str = str(views)

            self.info_label.setText(
                f"🎵 <b>{data.get('title', 'Desconhecido')}</b><br>"
                f"⏱ Duração: {data.get('duration', 'Desconhecido')}<br>"
                f"👤 Canal: {data.get('channel', 'Desconhecido')}<br>"
                f"👁 {views_str} visualizações"
            )

            # Carrega thumbnail
            thumbnail_url = data.get("thumbnail", "")
            if thumbnail_url:
                self.thumbnail_label.load_thumbnail(thumbnail_url)
            else:
                self.thumbnail_label.setText("📷")

            self.statusBar().showMessage("Vídeo encontrado!")
        else:
            # Usa informações básicas
            self.info_label.setText(
                f"🎵 <b>{basic_info.get('title', 'Desconhecido')}</b><br>"
                f"⏱ Duração: {basic_info.get('duration', 'Desconhecido')}<br>"
                f"👤 Canal: {basic_info.get('uploader', 'Desconhecido')}"
            )
            self.thumbnail_label.setText("📷")
            self.statusBar().showMessage("Vídeo encontrado!")

    def _start_download(self):
        """Inicia o download."""
        if self.is_downloading:
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira uma URL!")
            return

        # Salva configurações
        self._save_settings()

        # Atualiza diretório
        output_dir = self.dir_input.text().strip()
        if output_dir:
            self.downloader.set_output_dir(output_dir)

        # Verifica se é playlist
        if self._playlist_videos and len(self._playlist_videos) > 1:
            self._show_playlist_dialog()
            return

        # Download de vídeo único
        self._download_urls([url])

    def _show_playlist_dialog(self):
        """Mostra diálogo de seleção de playlist."""
        if self._playlist_videos:
            self.playlist_dialog = PlaylistDialog(self._playlist_videos, self)
            self.playlist_dialog.download_requested.connect(self._download_urls)
            self.playlist_dialog.show()

    def _download_urls(self, urls: list[str]):
        """Baixa uma lista de URLs."""
        self._set_downloading(True)
        self.item_label.setText("")

        is_audio = self.mode_combo.currentIndex() == 0
        audio_format = self.format_combo.currentText()
        quality = self.quality_combo.currentText()

        # Verifica se deve baixar legendas
        download_subs = self.subtitle_checkbox.isChecked()
        sub_lang = self.subtitle_lang.currentText()
        auto_subs = self.auto_sub_checkbox.isChecked()

        # Salva configurações de legendas para uso no download múltiplo
        self._download_subs = download_subs
        self._sub_lang = sub_lang
        self._auto_subs = auto_subs

        if len(urls) == 1:
            # Download único
            if is_audio:
                self.worker = WorkerThread(
                    self.downloader.download_audio, urls[0], audio_format, quality
                )
            else:
                self.worker = WorkerThread(
                    self.downloader.download_video, urls[0], video_quality=quality
                )
            self.worker.finished.connect(
                lambda ok, msg, data: self._on_download_finished(ok, msg, data, urls[0])
            )
            self.worker.start()

            # Adiciona ao histórico
            title = "Vídeo"
            if self._current_video_info:
                title = self._current_video_info.get("title", "Vídeo")
            self.settings.add_to_history(urls[0], title)
            self._update_history_combo()
        else:
            # Download múltiplo
            self.progress_label.setText(f"Preparando 0/{len(urls)}...")
            self._download_queue = urls
            self._download_index = 0
            self._download_success = 0
            self._download_failures = 0
            self._audio_format = audio_format
            self._audio_quality = quality
            self._is_audio_mode = is_audio
            self._download_next()

    def _download_next(self):
        """Baixa o próximo item da fila."""
        if self._download_index >= len(self._download_queue):
            self._on_multiple_download_finished()
            return

        if not self.is_downloading:
            return

        url = self._download_queue[self._download_index]
        total = len(self._download_queue)
        current = self._download_index + 1

        self.progress_label.setText(f"Baixando {current}/{total}...")
        self.item_label.setText(f"Item {current} de {total}")

        # Progresso geral da playlist
        overall_progress = int((self._download_index / total) * 100)
        self.progress_bar.setValue(overall_progress)

        if self._is_audio_mode:
            self.worker = WorkerThread(
                self.downloader.download_audio,
                url,
                self._audio_format,
                self._audio_quality,
            )
        else:
            self.worker = WorkerThread(
                self.downloader.download_video,
                url,
                video_quality=self._audio_quality,
            )
        self.worker.finished.connect(self._on_single_in_queue_finished)
        self.worker.start()

    def _on_single_in_queue_finished(self, success: bool, message: str, data):
        """Callback quando um item da fila termina."""
        if success:
            self._download_success += 1
        else:
            self._download_failures += 1
            self.logger.warning(f"Falha no item {self._download_index + 1}: {message}")

        self._download_index += 1
        self._download_next()

    def _on_download_finished(self, success: bool, message: str, data, url: str = ""):
        """Callback quando download único termina."""
        if success:
            # Baixa legendas se solicitado
            if hasattr(self, "_download_subs") and self._download_subs and url:
                self.statusBar().showMessage("Baixando legendas...")
                sub_ok, sub_msg, _ = self.downloader.download_subtitles(
                    url, self._sub_lang, self._auto_subs
                )
                if sub_ok:
                    self.logger.info(f"Legendas baixadas para: {url}")
                else:
                    self.logger.warning(f"Legendas não disponíveis: {sub_msg}")

            self._set_downloading(False)
            QMessageBox.information(self, "Sucesso", "✅ Download concluído!")
            self.statusBar().showMessage("Download concluído!")
            self.logger.info("Download concluído com sucesso")
        else:
            self._set_downloading(False)
            QMessageBox.critical(self, "Erro", f"❌ {message}")
            self.statusBar().showMessage("Erro no download")
            self.logger.error(f"Erro no download: {message}")

    def _on_multiple_download_finished(self):
        """Callback quando downloads múltiplos terminam."""
        self._set_downloading(False)

        msg = (
            f"✅ Downloads concluídos!\n\n"
            f"Sucesso: {self._download_success}\n"
            f"Falhas: {self._download_failures}"
        )
        QMessageBox.information(self, "Concluído", msg)

        self.statusBar().showMessage("Downloads concluídos!")
        self.progress_bar.setValue(100)
        self.item_label.setText(
            f"Concluído: {self._download_success} OK, {self._download_failures} falhas"
        )
        self.logger.info(
            f"Downloads concluídos: {self._download_success} sucesso, "
            f"{self._download_failures} falhas"
        )

    def _stop_download(self):
        """Para o download em andamento."""
        if self.is_downloading:
            self.downloader.stop()
            self._set_downloading(False)
            self.statusBar().showMessage("Download cancelado")
            self.logger.info("Download cancelado pelo usuário")

    def _set_downloading(self, downloading: bool):
        """Define estado de download."""
        self.is_downloading = downloading
        self.download_btn.setEnabled(not downloading)
        self.stop_btn.setEnabled(downloading)
        self.url_input.setEnabled(not downloading)
        self.fetch_btn.setEnabled(not downloading)
        self.format_combo.setEnabled(not downloading)
        self.quality_combo.setEnabled(not downloading)
        self.mode_combo.setEnabled(not downloading)

        if not downloading:
            self.downloader.reset()
            self.progress_bar.setValue(0)
            self.progress_label.setText("Pronto")

    def _on_progress(self, progress: dict):
        """Callback de progresso."""
        percent = progress.get("percent", 0)
        self.progress_bar.setValue(int(percent))
        self.progress_label.setText(f"Baixando... {percent:.1f}%")

    def _is_valid_youtube_url(self, url: str) -> bool:
        """Verifica se é uma URL válida do YouTube."""
        patterns = [
            "youtube.com/watch",
            "youtu.be/",
            "youtube.com/shorts/",
            "youtube.com/playlist",
            "music.youtube.com/",
        ]
        return any(p in url for p in patterns)

    def _show_logs(self):
        """Mostra janela de logs."""
        logs = self.logger.get_recent_logs(200)
        log_file = str(self.logger.get_log_file())

        msg = QMessageBox(self)
        msg.setWindowTitle("📋 Logs do Aplicativo")
        msg.setText(f"Arquivo de log: {log_file}")
        msg.setDetailedText(logs)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)

        # Aumenta tamanho da janela de detalhes
        msg.setStyleSheet("""
            QTextEdit {
                min-width: 600px;
                min-height: 400px;
                font-family: monospace;
            }
        """)
        msg.exec()

    def _open_search_dialog(self):
        """Abre o diálogo de busca no YouTube."""
        self.search_dialog = SearchDialog(self.downloader, self)
        self.search_dialog.video_selected.connect(self._on_search_video_selected)
        self.search_dialog.show()

    def _on_search_video_selected(self, url: str, title: str):
        """Quando um vídeo é selecionado na busca."""
        self.url_input.setText(url)
        self._fetch_info()

    def _open_queue_dialog(self):
        """Abre o diálogo de fila de downloads."""
        self.queue_dialog = DownloadQueueDialog(self)
        self.queue_dialog.start_downloads.connect(self._download_urls)
        self.queue_dialog.show()

    def run(self):
        """Mostra a janela."""
        self.show()


def main():
    """Função principal."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = YouTubeDownloaderApp()
    window.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
