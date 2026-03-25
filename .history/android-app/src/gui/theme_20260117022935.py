from kivymd.app import MDApp
from kivymd.theming import ThemeManager

class Theme:
    theme_cls = None

    @classmethod
    def setup(cls, app):
        app.theme_cls = ThemeManager()
        app.theme_cls.primary_palette = "Red"
        app.theme_cls.theme_style = "Dark"
        cls.theme_cls = app.theme_cls
