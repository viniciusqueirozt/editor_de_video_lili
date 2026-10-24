"""Preparação local de fotografias estáticas; o original permanece intacto."""
import warnings
from PIL import Image, ImageOps
from .core import EditorError

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
STILL_DURATION = 30


def prepare_still(source, output):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as image:
                if image.format not in ("JPEG", "PNG", "WEBP") or getattr(image, "is_animated", False):
                    raise EditorError("Importe uma foto JPG, PNG ou WebP estática.")
                if image.width * image.height > 50_000_000 or max(image.size) > 16384:
                    raise EditorError("A foto deve ter até 50 megapixels e 16384 pixels por lado.")
                image = ImageOps.exif_transpose(image)
                image.thumbnail((4096, 4096), Image.Resampling.LANCZOS)
                rgba = image.convert("RGBA")
                canvas = Image.new("RGB", rgba.size, "black")
                canvas.paste(rgba, mask=rgba.getchannel("A"))
                canvas.save(output, format="PNG")
                return {"duration": STILL_DURATION, "kind": "video", "has_audio": False,
                        "width": canvas.width, "height": canvas.height, "codec": "image",
                        "is_still": True, "still": output.name}
    except EditorError:
        raise
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise EditorError("Não foi possível abrir a foto. Confira o formato e a integridade do arquivo.", 422) from None
