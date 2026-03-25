#!/usr/bin/env python3
import urllib.request 
import subprocess
import tarfile 
import platform
from pathlib import Path

print("Setting up binaries...")
Path("binaries").mkdir(exist_ok=True)

# Download yt-dlp
print("Downloading yt-dlp...")
urllib.request.urlretrieve(
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp",
    "binaries/yt-dlp"
)
Path("binaries/yt-dlp").chmod(0o755)

# Download ffmpeg
print("Downloading ffmpeg...")
arch = "arm64" if platform.machine() == "aarch64" else "64"
urllib.request.urlretrieve(
    f"https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux{arch}-gpl.tar.xz",
    "binaries/ffmpeg.tar.xz"
)

print("Extracting ffmpeg...")
with tarfile.open("binaries/ffmpeg.tar.xz", 'r:xz') as tar:
    for member in tar.getmembers():
        if member.name.endswith('ffmpeg'):
            member.name = Path(member.name).name
            tar.extract(member, "binaries")

Path("binaries/ffmpeg.tar.xz").unlink()
Path("binaries/ffmpeg").chmod(0o755)
print("✓ Setup complete! Run ./run.sh")