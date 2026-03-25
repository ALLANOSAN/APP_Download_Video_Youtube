#!/usr/bin/env python3
"""Gerador de ícones PNG para a extensão Chrome"""

import os

# Dados PNG base64 para cada tamanho (ícone vermelho com play branco)
# Ícones criados programaticamente com cores sólidas


def create_icon_png(size: int) -> bytes:
    """Cria um ícone PNG simples"""
    import struct
    import zlib

    # Cria imagem com fundo vermelho (#FF0000) e triângulo branco
    width = height = size

    # Dados da imagem RGBA
    pixels = []

    center_x = size // 2
    center_y = size // 2

    for y in range(height):
        row = []
        for x in range(width):
            # Calcula se está dentro do triângulo play
            # Triângulo: ponta direita em (0.75*size, center), base em 0.35*size

            play_left = size * 0.35
            play_right = size * 0.75
            play_top = size * 0.25
            play_bottom = size * 0.75

            # Verifica se ponto está no triângulo
            in_triangle = False
            if play_left <= x <= play_right:
                # Altura relativa do triângulo neste x
                progress = (x - play_left) / (play_right - play_left)
                tri_height = (play_bottom - play_top) * (1 - progress)
                tri_center = (play_top + play_bottom) / 2
                if tri_center - tri_height / 2 <= y <= tri_center + tri_height / 2:
                    in_triangle = True

            # Verifica bordas arredondadas
            corner_radius = size * 0.2
            in_bounds = True

            # Cantos
            for cx, cy in [
                (corner_radius, corner_radius),
                (width - corner_radius, corner_radius),
                (corner_radius, height - corner_radius),
                (width - corner_radius, height - corner_radius),
            ]:
                if (x < corner_radius or x >= width - corner_radius) and (
                    y < corner_radius or y >= height - corner_radius
                ):
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if dist > corner_radius:
                        in_bounds = False
                        break

            if not in_bounds:
                row.extend([0, 0, 0, 0])  # Transparente
            elif in_triangle:
                row.extend([255, 255, 255, 255])  # Branco
            else:
                row.extend([255, 0, 0, 255])  # Vermelho

        pixels.append(bytes([0] + row))  # Filter byte + row data

    # Constrói PNG
    raw_data = b"".join(pixels)

    def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk_len = struct.pack(">I", len(data))
        chunk_crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return chunk_len + chunk_type + data + chunk_crc

    # PNG signature
    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = png_chunk(b"IHDR", ihdr_data)

    # IDAT chunk
    compressed = zlib.compress(raw_data, 9)
    idat = png_chunk(b"IDAT", compressed)

    # IEND chunk
    iend = png_chunk(b"IEND", b"")

    return signature + ihdr + idat + iend


def main():
    icons_dir = os.path.dirname(os.path.abspath(__file__))
    icons_path = os.path.join(icons_dir, "icons")
    os.makedirs(icons_path, exist_ok=True)

    for size in [16, 48, 128]:
        png_data = create_icon_png(size)
        filepath = os.path.join(icons_path, f"icon{size}.png")
        with open(filepath, "wb") as f:
            f.write(png_data)
        print(f"Created {filepath}")

    print("\nÍcones criados com sucesso!")
    print("Agora você pode carregar a extensão no Chrome:")
    print("1. Abra chrome://extensions/")
    print('2. Ative o "Modo do desenvolvedor"')
    print('3. Clique em "Carregar sem compactação"')
    print("4. Selecione a pasta chrome-extension/")


if __name__ == "__main__":
    main()
