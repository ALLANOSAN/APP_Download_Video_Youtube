"""
Gerador de ícone para o app Android YouTube Downloader Pro.
Cria ícones em vários tamanhos necessários para Android.
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon(size: int, output_path: str):
    """Cria um ícone com fundo gradiente e símbolo de download/play."""

    # Cria imagem com fundo
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Cores do tema
    bg_color_1 = (26, 26, 46)  # #1a1a2e - escuro
    bg_color_2 = (15, 52, 96)  # #0f3460 - azul escuro
    accent_color = (233, 69, 96)  # #e94560 - vermelho/rosa
    white = (255, 255, 255)

    # Desenha fundo com cantos arredondados
    radius = size // 5

    # Fundo principal (gradiente simulado com retângulos)
    for y in range(size):
        # Gradiente de cima para baixo
        ratio = y / size
        r = int(bg_color_1[0] * (1 - ratio) + bg_color_2[0] * ratio)
        g = int(bg_color_1[1] * (1 - ratio) + bg_color_2[1] * ratio)
        b = int(bg_color_1[2] * (1 - ratio) + bg_color_2[2] * ratio)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # Máscara para cantos arredondados
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    # Aplica máscara
    img.putalpha(mask)

    # Desenha círculo central (botão play)
    center = size // 2
    circle_radius = size // 3

    # Círculo vermelho/rosa
    draw.ellipse(
        [
            center - circle_radius,
            center - circle_radius,
            center + circle_radius,
            center + circle_radius,
        ],
        fill=accent_color,
    )

    # Triângulo de play (apontando para baixo = download)
    triangle_size = circle_radius * 0.7

    # Seta de download
    arrow_width = triangle_size * 0.6
    arrow_height = triangle_size * 0.8

    # Corpo da seta (retângulo)
    rect_width = arrow_width * 0.5
    rect_height = arrow_height * 0.6
    draw.rectangle(
        [
            center - rect_width / 2,
            center - arrow_height / 2,
            center + rect_width / 2,
            center + rect_height / 3,
        ],
        fill=white,
    )

    # Ponta da seta (triângulo)
    arrow_points = [
        (center, center + arrow_height / 2),  # Ponta inferior
        (center - arrow_width / 2, center),  # Esquerda
        (center + arrow_width / 2, center),  # Direita
    ]
    draw.polygon(arrow_points, fill=white)

    # Linha de base
    line_y = center + arrow_height / 2 + arrow_height * 0.15
    line_width = arrow_width * 0.8
    draw.rectangle(
        [center - line_width / 2, line_y, center + line_width / 2, line_y + arrow_height * 0.1],
        fill=white,
    )

    # Salva
    img.save(output_path, "PNG")
    print(f"✓ Criado: {output_path} ({size}x{size})")


def create_presplash(width: int, height: int, output_path: str):
    """Cria tela de splash/loading."""

    img = Image.new("RGB", (width, height), (26, 26, 46))
    draw = ImageDraw.Draw(img)

    # Texto centralizado
    text = "YouTube Downloader"
    text2 = "Pro"

    # Tenta usar fonte, senão usa padrão
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans.ttf", 40)
    except:
        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60
            )
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    # Desenha texto
    accent_color = (233, 69, 96)
    white = (255, 255, 255)

    # Emoji de música (como círculo simples)
    center_x = width // 2
    center_y = height // 2 - 100

    # Círculo do ícone
    icon_size = 80
    draw.ellipse(
        [center_x - icon_size, center_y - icon_size, center_x + icon_size, center_y + icon_size],
        fill=accent_color,
    )

    # Seta de download no círculo
    arrow_size = 50
    draw.polygon(
        [
            (center_x, center_y + arrow_size),
            (center_x - arrow_size * 0.7, center_y - arrow_size * 0.2),
            (center_x + arrow_size * 0.7, center_y - arrow_size * 0.2),
        ],
        fill=white,
    )

    draw.rectangle(
        [center_x - 15, center_y - arrow_size * 0.8, center_x + 15, center_y], fill=white
    )

    # Texto do título
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    draw.text((center_x - text_width // 2, center_y + 120), text, fill=white, font=font_large)

    bbox2 = draw.textbbox((0, 0), text2, font=font_small)
    text2_width = bbox2[2] - bbox2[0]
    draw.text(
        (center_x - text2_width // 2, center_y + 190), text2, fill=accent_color, font=font_small
    )

    img.save(output_path, "PNG")
    print(f"✓ Criado: {output_path} ({width}x{height})")


def main():
    """Gera todos os ícones necessários."""

    # Diretório de saída
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Ícones Android (vários tamanhos)
    icon_sizes = [
        (48, "icon-48.png"),
        (72, "icon-72.png"),
        (96, "icon-96.png"),
        (144, "icon-144.png"),
        (192, "icon-192.png"),
        (512, "icon.png"),  # Ícone principal
    ]

    print("🎨 Gerando ícones...")

    for size, filename in icon_sizes:
        output_path = os.path.join(output_dir, filename)
        create_icon(size, output_path)

    # Presplash (tela de loading)
    print("\n🖼 Gerando presplash...")
    presplash_path = os.path.join(output_dir, "presplash.png")
    create_presplash(1080, 1920, presplash_path)

    print("\n✅ Todos os assets foram criados!")
    print(f"📁 Diretório: {output_dir}")


if __name__ == "__main__":
    main()
