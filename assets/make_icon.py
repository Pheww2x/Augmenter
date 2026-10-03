"""Run once to generate assets/icon.ico"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def make_icon():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    draw.ellipse([4, 4, size - 4, size - 4], fill=(20, 20, 50, 255), outline=(90, 90, 180, 255), width=4)

    # Draw three small image rectangles suggesting augmentation
    rects = [
        (30, 80, 100, 150),
        (78, 60, 148, 130),
        (126, 80, 196, 150),
    ]
    colors = [(60, 60, 140), (80, 80, 180), (100, 100, 220)]
    for rect, color in zip(rects, colors):
        draw.rectangle(rect, fill=color, outline=(150, 150, 255), width=2)
        # mini landscape inside
        draw.rectangle(
            [rect[0] + 6, rect[1] + 6, rect[2] - 6, rect[3] - 6],
            fill=(color[0] + 20, color[1] + 20, color[2] + 20),
        )

    # Arrow suggesting transformation
    arrow_y = 170
    draw.polygon(
        [(90, arrow_y), (166, arrow_y), (166, arrow_y - 10),
         (190, arrow_y + 10), (166, arrow_y + 30), (166, arrow_y + 20), (90, arrow_y + 20)],
        fill=(123, 140, 222, 220),
    )

    # Text
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    draw.text((size // 2, 215), "AUGMENTER", fill=(180, 190, 255), font=font, anchor="mm")

    out = Path(__file__).parent / "icon.ico"
    out.parent.mkdir(exist_ok=True)
    img.save(out, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print(f"Icon saved to {out}")


if __name__ == "__main__":
    make_icon()
