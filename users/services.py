import io
import random
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

AVATAR_COLORS = [
    (100, 149, 237),
    (60, 179, 113),
    (255, 127, 80),
    (147, 112, 219),
    (255, 215, 0),
    (255, 99, 71),
    (0, 191, 255),
    (128, 0, 128),
    (46, 139, 87),
]


def generate_user_avatar(user):
    """
    Generates a simple placeholder avatar image based on the user's first name.
    The image consists of a random background color and the first letter of the name.
    """
    bg_color = random.choice(AVATAR_COLORS)
    size = (200, 200)
    image = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(image)

    text = user.name[0].upper() if user.name else "?"

    try:
        font = ImageFont.truetype("arial.ttf", 100)
    except IOError:
        font = ImageFont.load_default()

    w, h = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text(((size[0] - w) / 2, (size[1] - h) / 2), text, fill="white", font=font)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    filename = f'avatar_{user.pk or "new"}.png'
    return filename, ContentFile(buffer.getvalue())
