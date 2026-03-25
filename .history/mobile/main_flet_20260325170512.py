import flet as ft
import sys
import os
import stat
import httpx
import asyncio
from pathlib import Path

# Configura caminho dos binários mobile para YT-DLP/FFMPEG
binary_root = Path(__file__).resolve().parent.parent / "binaries"
if binary_root.exists():
    yt_dlp_bin = binary_root / "yt-dlp"
    ffmpeg_bin = binary_root / "ffmpeg"
    if yt_dlp_bin.exists():
        os.environ["YT_DLP_PATH"] = str(yt_dlp_bin)
        yt_dlp_bin.chmod(yt_dlp_bin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if ffmpeg_bin.exists():
        os.environ["FFMPEG_PATH"] = str(ffmpeg_bin)
        ffmpeg_bin.chmod(ffmpeg_bin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Adiciona o diretório raiz ao path para importar o downloader
sys.path.append(str(Path(__file__).parent.parent))

# Tenta importar o downloader
try:
    from src.downloader.video_downloader import VideoDownloader
except ImportError:
    sys.path.append(os.getcwd())
    from src.downloader.video_downloader import VideoDownloader


def main(page: ft.Page):
    page.title = "YouTube Music Pro Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 800
    page.padding = 0
    page.spacing = 0

    # Design Tokens (Premium Palette)
    ACCENT = "#2DD4BF"  # Teal
    SURFACE = "#1E293B"  # Deep Slate
    BG = "#0F172A"  # Navy
    TEXT_DIM = "#94A3B8"

    page.bgcolor = BG

    downloader = VideoDownloader()

    # API Config
    # Se estiver no emulador Android, use 10.0.2.2 para acessar o localhost do PC
    # Se estiver em produção, substitua pela URL do seu servidor (ex: Render, Railway)
    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

    class SyncClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.token = None

        async def login(self, username, password):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/auth/token",
                        data={"username": username, "password": password},
                    )
                    if response.status_code == 200:
                        self.token = response.json()["access_token"]
                        return True, "Logado com sucesso!"
                    return False, f"Erro: {response.json().get('detail', 'Falha no login')}"
            except Exception as e:
                return False, f"Erro de conexão: {e}"

        async def get_history(self):
            if not self.token:
                return []
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/history",
                        headers={"Authorization": f"Bearer {self.token}"},
                    )
                    return response.json() if response.status_code == 200 else []
            except Exception:
                return []

        async def add_history(self, title, url, thumbnail="", uploader=""):
            if not self.token:
                return
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.base_url}/history",
                        headers={"Authorization": f"Bearer {self.token}"},
                        json={
                            "video_id": url.split("=")[-1],
                            "title": title,
                            "url": url,
                            "thumbnail": thumbnail,
                            "uploader": uploader,
                        },
                    )
            except Exception:
                pass

    sync_client = SyncClient(API_URL)

    # --- Skeleton Screen Component ---
    def create_skeleton_card():
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=100, height=60, bgcolor="#334155", border_radius=8),
                    ft.Column(
                        [
                            ft.Container(width=150, height=15, bgcolor="#334155", border_radius=4),
                            ft.Container(width=80, height=10, bgcolor="#334155", border_radius=4),
                        ],
                        spacing=8,
                        expand=True,
                    ),
                ]
            ),
            padding=12,
            bgcolor=SURFACE,
            border_radius=16,
            animate=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        )

    # --- UI Components ---
    search_field = ft.TextField(
        hint_text="Busque músicas ou vídeos...",
        border_radius=16,
        border_color="#334155",
        bgcolor=SURFACE,
        suffix_icon=ft.icons.SEARCH_ROUNDED,
        content_padding=16,
        on_submit=lambda e: do_search(e.control.value),
        border_width=1,
        focused_border_color=ACCENT,
    )

    results_list = ft.ListView(expand=True, spacing=12, padding=20)

    def do_search(query):
        if not query:
            return

        # Estado de Carregamento (Skeletons)
        results_list.controls.clear()
        for _ in range(5):
            results_list.controls.append(create_skeleton_card())
        page.update()

        try:
            success, message, results = downloader.search_youtube(query, max_results=5)

            results_list.controls.clear()
            if success and results:
                for item in results:
                    video_url = item.get("url", "")

                    # Card Premium com Animação de Entrada
                    card = ft.Container(
                        content=ft.Row(
                            [
                                ft.Image(
                                    src=item.get("thumbnail", ""),
                                    width=110,
                                    height=65,
                                    fit=ft.ImageFit.COVER,
                                    border_radius=8,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(
                                            item.get("title", "Vídeo"),
                                            weight=ft.FontWeight.BOLD,
                                            size=14,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                        ),
                                        ft.Text(
                                            item.get("uploader", "Canal"), size=12, color=TEXT_DIM
                                        ),
                                    ],
                                    spacing=4,
                                    expand=True,
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=12,
                        bgcolor=SURFACE,
                        border_radius=16,
                        ink=True,  # Feedback visual de toque
                        on_click=lambda _,
                        url=video_url,
                        t=item.get("title"),
                        img=item.get("thumbnail"),
                        up=item.get("uploader"): asyncio.create_task(
                            handle_download(t, url, img, up)
                        ),
                        offset=ft.Offset(0, 0.1),
                        animate_offset=ft.Animation(400, ft.AnimationCurve.DECELERATE),
                        opacity=0,
                        animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN),
                    )

                    results_list.controls.append(card)
                    page.update()

                    # Trigger animation
                    card.offset = ft.Offset(0, 0)
                    card.opacity = 1
                    page.update()

            else:
                results_list.controls.append(
                    ft.Container(
                        content=ft.Text(
                            f"Ops! {message}",
                            color=ft.colors.RED_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        padding=20,
                        alignment=ft.alignment.center,
                    )
                )
        except Exception as e:
            results_list.controls.append(ft.Text(f"Erro inesperado: {e}", color="red"))

        page.update()

    def show_message(text):
        snack = ft.SnackBar(
            content=ft.Text(text, color=BG), bgcolor=ACCENT, action="OK", action_color=BG
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    async def handle_download(title, url, thumb, uploader):
        show_message(f"Baixando: {title}")
        if sync_client.token:
            await sync_client.add_history(title, url, thumb, uploader)
            await update_library()

    async def update_library():
        if not sync_client.token:
            library_list.controls = [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.LOCK_OUTLINED, size=50, color=TEXT_DIM),
                            ft.Text("Faça login para ver sua biblioteca", color=TEXT_DIM),
                            ft.ElevatedButton("Login", on_click=lambda _: show_login_dialog()),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            ]
        else:
            history = await sync_client.get_history()
            library_list.controls.clear()
            if not history:
                library_list.controls.append(
                    ft.Text("Nenhum download sincronizado.", color=TEXT_DIM)
                )
            for item in history:
                library_list.controls.append(
                    ft.ListTile(
                        leading=ft.Image(src=item["thumbnail"], width=60, border_radius=4),
                        title=ft.Text(item["title"], size=14, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(item["uploader"], size=12, color=TEXT_DIM),
                        bgcolor=SURFACE,
                    )
                )
        page.update()

    library_list = ft.ListView(expand=True, spacing=10, padding=20)

    # --- Login Dialog ---
    user_input = ft.TextField(label="Usuário", border_color=ACCENT)
    pass_input = ft.TextField(
        label="Senha", password=True, can_reveal_password=True, border_color=ACCENT
    )

    def close_dlg(e):
        login_dlg.open = False
        page.update()

    async def do_login(e):
        success, msg = await sync_client.login(user_input.value, pass_input.value)
        show_message(msg)
        if success:
            login_dlg.open = False
            await update_library()
        page.update()

    login_dlg = ft.AlertDialog(
        title=ft.Text("Entrar na Conta Sync"),
        content=ft.Column([user_input, pass_input], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=close_dlg),
            ft.ElevatedButton("Entrar", bgcolor=ACCENT, color=BG, on_click=do_login),
        ],
    )

    def show_login_dialog():
        page.dialog = login_dlg
        login_dlg.open = True
        page.update()

    # --- Header Premium ---
    header = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            "Descobrir", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE
                        ),
                        ft.IconButton(
                            ft.icons.PERSON_ROUNDED,
                            icon_color=TEXT_DIM,
                            on_click=lambda _: show_login_dialog(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                search_field,
            ]
        ),
        padding=ft.padding.only(top=40, left=20, right=20, bottom=10),
        bgcolor=BG,
    )

    # --- Bottom Navigation Logic ---
    main_content = ft.Container(content=ft.Column([header, results_list], expand=True), expand=True)

    def on_nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            main_content.content = ft.Column([header, results_list], expand=True)
        elif idx == 1:
            main_content.content = ft.Column(
                [
                    ft.Container(
                        ft.Text("Biblioteca", size=28, weight=ft.FontWeight.BOLD), padding=20
                    ),
                    library_list,
                ],
                expand=True,
            )
            asyncio.create_task(update_library())
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.EXPLORE_ROUNDED, label="Explorar"),
            ft.NavigationDestination(icon=ft.icons.LIBRARY_MUSIC_ROUNDED, label="Biblioteca"),
            ft.NavigationDestination(icon=ft.icons.DOWNLOAD_DONE_ROUNDED, label="Downloads"),
        ],
        bgcolor=SURFACE,
        selected_index=0,
        indicator_color=ACCENT,
        on_change=on_nav_change,
    )

    page.add(main_content)


if __name__ == "__main__":
    ft.app(target=main)
