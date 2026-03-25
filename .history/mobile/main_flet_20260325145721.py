import flet as ft
import sys
import os
from pathlib import Path

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
    SURFACE = "#1E293B" # Deep Slate
    BG = "#0F172A"      # Navy
    TEXT_DIM = "#94A3B8"

    page.bgcolor = BG

    downloader = VideoDownloader()

    # --- Skeleton Screen Component ---
    def create_skeleton_card():
        return ft.Container(
            content=ft.Row([
                ft.Container(width=100, height=60, bgcolor="#334155", border_radius=8),
                ft.Column([
                    ft.Container(width=150, height=15, bgcolor="#334155", border_radius=4),
                    ft.Container(width=80, height=10, bgcolor="#334155", border_radius=4),
                ], spacing=8, expand=True)
            ]),
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
                    video_url = item.get('url', '')

                    # Card Premium com Animação de Entrada
                    card = ft.Container(
                        content=ft.Row([
                            ft.Image(
                                src=item.get('thumbnail', ''),
                                width=110,
                                height=65,
                                fit=ft.ImageFit.COVER,
                                border_radius=8
                            ),
                            ft.Column([
                                ft.Text(
                                    item.get('title', 'Vídeo'),
                                    weight=ft.FontWeight.BOLD,
                                    size=14,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                ft.Text(
                                    item.get('uploader', 'Canal'),
                                    size=12,
                                    color=TEXT_DIM
                                ),
                            ], spacing=4, expand=True)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=12,
                        bgcolor=SURFACE,
                        border_radius=16,
                        ink=True,  # Feedback visual de toque
                        on_click=lambda _, url=video_url: show_message(f"Adicionado` : {url}"),
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
                            text_align=ft.TextAlign.CENTER
                        ),
                        padding=20,
                        alignment=ft.alignment.center
                    )
                )
        except Exception as e:
            results_list.controls.append(ft.Text(f"Erro inesperado: {e}", color="red"))

        page.update()

    def show_message(text):
        snack = ft.SnackBar(
            content=ft.Text(text, color=BG),
            bgcolor=ACCENT,
            action="OK",
            action_color=BG
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- Header Premium ---
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Descobrir", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                ft.IconButton(ft.icons.PERSON_ROUNDED, icon_color=TEXT_DIM)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            search_field,
        ]),
        padding=ft.padding.only(top=40, left=20, right=20, bottom=10),
        bgcolor=BG
    )

    # --- Bottom Navigation ---
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.EXPLORE_ROUNDED, label="Explorar"),
            ft.NavigationDestination(icon=ft.icons.LIBRARY_MUSIC_ROUNDED, label="Biblioteca"),
            ft.NavigationDestination(icon=ft.icons.DOWNLOAD_DONE_ROUNDED, label="Downloads"),
        ],
        bgcolor=SURFACE,
        selected_index=0,
        indicator_color=ACCENT,
    )

    page.add(
        ft.Column([
            header,
            results_list
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
