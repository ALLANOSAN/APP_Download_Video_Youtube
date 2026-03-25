#!/usr/bin/env python3
"""
Script para criar executável Linux com ffmpeg e yt-dlp embutidos.

Uso:
    python build_linux.py

Isso irá:
1. Baixar yt-dlp e ffmpeg para a pasta binaries/
2. Criar o executável com PyInstaller incluindo os binários
"""

import platform
import stat
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path


def download_file(url: str, dest: Path) -> None:
    """Baixa um arquivo da URL para o destino."""
    print(f"  Baixando: {url}")
    urllib.request.urlretrieve(url, dest)


def setup_binaries() -> Path:
    """Baixa e configura os binários necessários."""
    binaries_dir = Path("binaries")
    binaries_dir.mkdir(exist_ok=True)
    
    # Download yt-dlp
    ytdlp_path = binaries_dir / "yt-dlp"
    if not ytdlp_path.exists():
        print("📥 Baixando yt-dlp...")
        download_file(
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp",
            ytdlp_path
        )
        ytdlp_path.chmod(ytdlp_path.stat().st_mode | stat.S_IEXEC)
        print("  ✓ yt-dlp baixado")
    else:
        print("✓ yt-dlp já existe")
    
    # Download ffmpeg
    ffmpeg_path = binaries_dir / "ffmpeg"
    if not ffmpeg_path.exists():
        print("📥 Baixando ffmpeg...")
        arch = "arm64" if platform.machine() == "aarch64" else "64"
        ffmpeg_url = f"https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux{arch}-gpl.tar.xz"
        
        tar_path = binaries_dir / "ffmpeg.tar.xz"
        download_file(ffmpeg_url, tar_path)
        
        print("  Extraindo ffmpeg...")
        with tarfile.open(tar_path, 'r:xz') as tar:
            for member in tar.getmembers():
                if member.name.endswith('/ffmpeg') and member.isfile():
                    member.name = "ffmpeg"
                    tar.extract(member, binaries_dir)
                    break
                elif member.name.endswith('/ffprobe') and member.isfile():
                    member.name = "ffprobe"
                    tar.extract(member, binaries_dir)
        
        # Limpa arquivo temporário
        tar_path.unlink()
        
        # Torna executável
        ffmpeg_path.chmod(ffmpeg_path.stat().st_mode | stat.S_IEXEC)
        ffprobe_path = binaries_dir / "ffprobe"
        if ffprobe_path.exists():
            ffprobe_path.chmod(ffprobe_path.stat().st_mode | stat.S_IEXEC)
        
        print("  ✓ ffmpeg extraído")
    else:
        print("✓ ffmpeg já existe")
    
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
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Binários a serem incluídos
binaries_to_add = [
    ('{binaries_dir}/yt-dlp', 'binaries'),
    ('{binaries_dir}/ffmpeg', 'binaries'),
]

# Adiciona ffprobe se existir
import os
if os.path.exists('{binaries_dir}/ffprobe'):
    binaries_to_add.append(('{binaries_dir}/ffprobe', 'binaries'))

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=binaries_to_add,
    datas=[],
    hiddenimports=['gui', 'gui.main_window', 'downloader', 'downloader.video_downloader'],
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
)
'''
    
    spec_path = Path("YouTubeDownloader.spec")
    spec_path.write_text(spec_content)
    return spec_path


def build_executable(spec_path: Path) -> None:
    """Compila o executável usando PyInstaller."""
    print("🔨 Compilando executável...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path)
    ]
    
    subprocess.run(cmd, check=True)
    print("  ✓ Executável criado")


def main():
    print("=" * 50)
    print("🚀 Build YouTube Downloader para Linux")
    print("=" * 50)
    print()
    
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
    print("  ✓ YouTubeDownloader.spec criado")
    
    print()
    
    # Compila
    build_executable(spec_path)
    
    print()
    print("=" * 50)
    print("✅ Build concluído!")
    print()
    print("O executável está em: dist/YouTubeDownloader")
    print()
    print("Para executar:")
    print("  ./dist/YouTubeDownloader")
    print("=" * 50)


if __name__ == "__main__":
    main()
