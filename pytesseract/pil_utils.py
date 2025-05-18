"""PIL utilities"""

from collections import namedtuple
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from PIL.Image import Image

from .api import get_text, TesseractOptions


Rect = namedtuple("Rect", ["left", "upper", "right", "lower"])
"""tuple of (left, upper, right, lower)"""


@dataclass
class PILOptions:
    black_threshold: int = 128
    rotate_angle: Optional[float] = 0
    crop_rect: Optional[Rect] = None

    def apply(self, image: Image) -> Image:
        """apply to image"""

        image = image.convert("L")
        image = image.point(lambda x: 0 if x < self.black_threshold else 255)

        if angle := self.rotate_angle:
            image = image.rotate(angle)
        if rect := self.crop_rect:
            image = image.crop(*rect)

        return image


DefaultPILOptions = PILOptions()


def get_text_from_image(
    image: Image,
    *,
    ocr_options: Optional[TesseractOptions] = None,
    pil_options: Optional[PILOptions] = DefaultPILOptions,
    **kwargs,
) -> str:
    """get text from PIL image"""

    image = pil_options.apply(image)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return get_text(buffer, options=ocr_options, **kwargs)
