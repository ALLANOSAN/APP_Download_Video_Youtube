#!/usr/bin/env python3
"""
Script para criar executável Windows com ffmpeg e yt-dlp embutidos.

Uso (no Windows):
    python build_windows.py

Isso irá:
1. Baixar yt-dlp.exe e ffmpeg.exe para a pasta binaries/
2. Criar o executável com PyInstaller incluindo os binários
"""

import subprocess
import sys
import zipfile
import urllib.request
from pathlib import Path


def download_file(url: str, dest: Path) -> None:
    """Baixa um arquivo da URL para o destino."""
    print(f"  Baixando: {url}")
    urllib.request.urlretrieve(url, dest)


def setup_binaries() -> Path:
    """Baixa e configura os binários necessários para Windows."""
    binaries_dir = Path("binaries")
    binaries_dir.mkdir(exist_ok=True)

    # Download yt-dlp
    ytdlp_path = binaries_dir / "yt-dlp.exe"
    if not ytdlp_path.exists():
        print("📥 Baixando yt-dlp.exe...")
        download_file(
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
            ytdlp_path,
        )
        print("  ✓ yt-dlp.exe baixado")
    else:
        print("✓ yt-dlp.exe já existe")

    # Download ffmpeg
    ffmpeg_path = binaries_dir / "ffmpeg.exe"
    if not ffmpeg_path.exists():
        print("📥 Baixando ffmpeg...")
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

        zip_path = binaries_dir / "ffmpeg.zip"
        download_file(ffmpeg_url, zip_path)

        print("  Extraindo ffmpeg...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.namelist():
                if file_info.endswith("ffmpeg.exe"):
                    with zip_ref.open(file_info) as src:
                        with open(binaries_dir / "ffmpeg.exe", "wb") as dst:
                            dst.write(src.read())
                elif file_info.endswith("ffprobe.exe"):
                    with zip_ref.open(file_info) as src:
                        with open(binaries_dir / "ffprobe.exe", "wb") as dst:
                            dst.write(src.read())

        # Limpa arquivo temporário
        zip_path.unlink()
        print("  ✓ ffmpeg extraído")
    else:
        print("✓ ffmpeg.exe já existe")

    return binaries_dir


def check_pyinstaller() -> bool:
    """Verifica se PyInstaller está instalado."""
    import importlib.util

    return importlib.util.find_spec("PyInstaller") is not None


def install_pyinstaller() -> None:
    """Instala PyInstaller usando uv."""
    print("📦 Instalando PyInstaller...")
    subprocess.run(["uv", "pip", "install", "pyinstaller"], check=True)
    print("  ✓ PyInstaller instalado")


def create_spec_file(binaries_dir: Path) -> Path:
    """Cria o arquivo .spec para o PyInstaller."""
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Binários a serem incluídos
binaries_to_add = [
    ('{binaries_dir}/yt-dlp.exe', 'binaries'),
    ('{binaries_dir}/ffmpeg.exe', 'binaries'),
]

# Adiciona ffprobe se existir
import os
if os.path.exists('{binaries_dir}/ffprobe.exe'):
    binaries_to_add.append(('{binaries_dir}/ffprobe.exe', 'binaries'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_to_add,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={{}},
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
    icon=None,  # Pode adicionar um ícone aqui: icon='icon.ico'
)
"""

    spec_path = Path("YouTubeDownloader_win.spec")
    spec_path.write_text(spec_content)
    return spec_path


def build_executable(spec_path: Path) -> None:
    """Compila o executável usando PyInstaller."""
    print("🔨 Compilando executável...")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]

    subprocess.run(cmd, check=True)
    print("  ✓ Executável criado")


def main():
    print("=" * 50)
    print("🚀 Build YouTube Downloader para Windows")
    print("=" * 50)
    print()

    # Verifica se está no Windows
    if sys.platform != "win32":
        print("⚠️  Este script deve ser executado no Windows!")
        print("   Para Linux, use: python build_linux.py")
        return

    # Verifica/instala PyInstaller
    if not check_pyinstaller():
        install_pyinstaller()
    else:
        print("✓ PyInstaller já instalado")

    print()

    # Baixa binários
    binaries_dir = setup_binaries()

    print()

    # Cria arquivo .spec
    print("📝 Criando arquivo de configuração...")
    spec_path = create_spec_file(binaries_dir)
    print("  ✓ YouTubeDownloader_win.spec criado")

    print()

    # Compila
    build_executable(spec_path)

    print()
    print("=" * 50)
    print("✅ Build concluído!")
    print()
    print("O executável está em: dist\\YouTubeDownloader.exe")
    print("=" * 50)


if __name__ == "__main__":
    main()
