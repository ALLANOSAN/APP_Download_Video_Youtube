# Suporte a compartilhamento de links do YouTube via intent SEND
from kivy.utils import platform

# No Android, o link compartilhado pode ser recuperado via sys.argv
import sys


def get_shared_youtube_link():
    if platform == "android" and len(sys.argv) > 1:
        arg = sys.argv[1]
        if "youtube.com" in arg or "youtu.be" in arg:
            return arg
    return None
