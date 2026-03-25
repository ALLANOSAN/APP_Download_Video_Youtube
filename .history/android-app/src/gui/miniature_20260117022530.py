# Widget para exibir miniatura e título destacado
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label

class Miniature(BoxLayout):
    def __init__(self, title, thumb_url, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=80, **kwargs)
        self.add_widget(AsyncImage(source=thumb_url, size_hint_x=None, width=120))
        self.add_widget(Label(text=title, halign='left', valign='middle'))
