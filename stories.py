from PIL import Image, ImageFilter, ImageFont, ImageDraw, ImageOps
import wget
import io
import base64
import os


def prepare_storie(url, name):
    filename = wget.download(url)

    original = Image.open(filename)
    blurred = original.filter(ImageFilter.GaussianBlur(10))
    blurred = ImageOps.fit(blurred, (720, 1280))
    (width, height) = blurred.size

    original.thumbnail((720, 500), Image.ANTIALIAS)
    (w, h) = original.size
    blurred.paste(original, ((width - w)//2, (height - h)//2))

    font = ImageFont.truetype("OpenSans-Regular.ttf", 40)
    font_b = ImageFont.truetype("OpenSans-Regular.ttf", 40)

    draw = ImageDraw.Draw(blurred)
    draw.text((80 - 1, 900 + 1), "Я сижу дома и поддерживаю\n" + "петицию\n" + name, (0, 0, 0), font=font_b, align='center')
    draw.text((80 + 1, 900 - 1), "Я сижу дома и поддерживаю\n" + "петицию\n" + name, (0, 0, 0), font=font_b, align='center')
    draw.text((80 + 1, 900 + 1), "Я сижу дома и поддерживаю\n" + "петицию\n" + name, (0, 0, 0), font=font_b, align='center')
    draw.text((80 - 1, 900 - 1), "Я сижу дома и поддерживаю\n" + "петицию\n" + name, (0, 0, 0), font=font_b, align='center')
    draw.text((80, 900), "Я сижу дома и поддерживаю\n" + "петицию\n" + name, (255, 255, 255), font=font, align='center')

    buffered = io.BytesIO()
    blurred.save(buffered, format=original.format)
    img_str = base64.b64encode(buffered.getvalue())
    os.remove(filename)
    return {'image': str(img_str)}
