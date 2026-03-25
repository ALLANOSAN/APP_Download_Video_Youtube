# Histórico de buscas e downloads
import os
import json

HISTORY_FILE = os.path.expanduser("~/.yt_downloader_history.json")


def add_history(entry):
    history = get_history()
    history.insert(0, entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:100], f)


def get_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE) as f:
        return json.load(f)
