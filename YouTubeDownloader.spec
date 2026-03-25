# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Binários a serem incluídos
binaries_to_add = [
    ('binaries/yt-dlp', 'binaries'),
    ('binaries/ffmpeg', 'binaries'),
]

# Adiciona ffprobe se existir
import os
if os.path.exists('binaries/ffprobe'):
    binaries_to_add.append(('binaries/ffprobe', 'binaries'))

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=binaries_to_add,
    datas=[],
    hiddenimports=[
        'gui', 'gui.main_window',
        'downloader', 'downloader.video_downloader',
        'utils', 'utils.settings', 'utils.logger',
        'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YouTubeDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
