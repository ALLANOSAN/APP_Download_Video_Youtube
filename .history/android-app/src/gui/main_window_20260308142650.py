# Tela principal do app: busca, resultados, seleção de formato e download

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarListItem, ImageLeftWidget
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivy.clock import mainthread
import threading

class MainWindow(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.search_input = MDTextField(hint_text='Buscar vídeo no YouTube...', size_hint_y=None, height=50)
        self.search_btn = MDRaisedButton(text='Buscar', size_hint_y=None, height=50)
        self.search_btn.bind(on_release=self.on_search)
        self.history_btn = MDFlatButton(text='Histórico', size_hint_y=None, height=50)
        self.history_btn.bind(on_release=self.show_history)
        top_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        top_bar.add_widget(self.search_input)
        top_bar.add_widget(self.search_btn)
        top_bar.add_widget(self.history_btn)
        self.add_widget(top_bar)
            def show_history(self, instance):
                from src.gui.history import get_history
                from kivymd.uix.list import OneLineListItem
                history = get_history()
                items = []
                for entry in history:
                    text = f"{entry.get('title', '')} - {entry.get('url', '')}"
                    items.append(OneLineListItem(text=text))
                dialog = MDDialog(title='Histórico', type='simple', items=items)
                dialog.open()
        self.progress = MDProgressBar(value=0, max=100, size_hint_y=None, height=4)
        self.add_widget(self.progress)
        self.results_area = MDScrollView(size_hint=(1, 1))
        from kivymd.uix.list import MDList
        self.results_list = MDList()
        self.results_area.add_widget(self.results_list)
        self.add_widget(self.results_area)
        
        # Se iniciado via compartilhamento, abrir tela de formatos direto
        from src.gui.share_intent import get_shared_youtube_link
        shared_link = get_shared_youtube_link()
        if shared_link:
            self.show_format_popup({'title': 'YouTube Link Compartilhado', 'url': shared_link})

    def on_search(self, instance):
        query = self.search_input.text.strip()
        if not query:
            return
        self.results_list.clear_widgets()
        from src.downloader.search import search_youtube
        results = search_youtube(query)
        # Salva busca no histórico
        from src.gui.history import add_history
        add_history({'type': 'busca', 'query': query, 'result_count': len(results)})
        for video in results:
            item = OneLineAvatarListItem(text=video['title'])
            if 'thumbnail' in video:
                item.add_widget(ImageLeftWidget(source=video['thumbnail']))
            item.bind(on_release=lambda btn, v=video: self.show_format_popup(v))
            self.results_list.add_widget(item)

    def show_format_popup(self, video):
        from src.downloader.formats import get_formats
        formats = get_formats(video['url'])
        items = []
        for f in formats:
            items.append({
                'text': f"{f['type']} {f['format']} {f['desc']}",
                'on_release': lambda x=None, fmt=f: self.download_selected(video, fmt)
            })
        self.dialog = MDDialog(
            title='Escolha o formato',
            type='simple',
            items=[MDFlatButton(text=i['text'], on_release=i['on_release']) for i in items],
        )
        self.dialog.open()

    def download_selected(self, video, fmt):
        self.dialog.dismiss()
        from src.downloader.download import download_video
        self.progress.value = 0
        def run_download():
            try:
                download_video(video['url'], fmt, self.update_progress)
                # Salva download no histórico
                from src.gui.history import add_history
                add_history({'type': 'download', 'title': video.get('title', ''), 'url': video['url'], 'format': fmt})
                self.show_notification('Download finalizado!')
            except Exception as e:
                self.show_notification(f'Erro: {e}')
        threading.Thread(target=run_download, daemon=True).start()

    @mainthread
    def update_progress(self, percent):
        self.progress.value = percent

    @mainthread
    def show_notification(self, msg):
        from kivymd.toast import toast
        toast(msg)

class YouTubeDownloaderApp(MDApp):
    def build(self):
        return MainWindow()

if __name__ == '__main__':
    YouTubeDownloaderApp().run()
