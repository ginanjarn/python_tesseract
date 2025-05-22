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
    grayscale: bool = False
    """convert image to grayscale"""

    binarize: bool = False
    """binarize image to 0 (black) or 255 (white) based on white_threshold"""
    white_threshold: int = 128
    """"""

    rotate_angle: Optional[float] = 0
    """rotate image"""

    crop_rect: Optional[Rect] = None
    """crop image with defined rectangle"""

    def apply(self, image: Image) -> Image:
        """apply options to image"""

        if self.binarize:
            image = image.point(lambda x: 0 if x < self.white_threshold else 255)

        # ignore grayscale if image has been binarized
        if self.grayscale and (not self.binarize):
            image = image.convert("L")

        if angle := self.rotate_angle:
            image = image.rotate(angle)

        if rect := self.crop_rect:
            image = image.crop(*rect)

        return image


DefaultPILOptions = PILOptions()


def get_text_from_image(
    image: Image,
    *,
    tesseract_options: Optional[TesseractOptions] = None,
    pil_options: Optional[PILOptions] = DefaultPILOptions,
    **kwargs,
) -> str:
    """get text from PIL image"""

    image = pil_options.apply(image)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return get_text(buffer, options=tesseract_options, **kwargs)
