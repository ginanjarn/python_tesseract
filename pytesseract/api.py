"""Tesseract API

For more information see:
  https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc

"""

import os
import re
import subprocess
from dataclasses import dataclass, fields
from enum import Enum, IntEnum, StrEnum
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Dict, Union, Any


# Get tesseract executable from environment
TESSERACT_PATH = os.environ.get("TESSERACT_PATH") or "tesseract"

if os.name == "nt":
    STARTUPINFO = subprocess.STARTUPINFO()
    # Hide created process window
    STARTUPINFO.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW
else:
    STARTUPINFO = None


def run_tesseract(
    arguments: List[str],
    *,
    stdin: Optional[BytesIO] = None,
    env: Optional[dict] = None,
    cwd: Optional[Path] = None,
) -> str:
    """run tesseract

    Tesseract arguments:

      <TESSERACT> --help | --help-extra | --version
      <TESSERACT> --list-langs
      <TESSERACT> INPUT OUTPUT [OPTIONS...] [CONFIGFILE...]

    To work with standard IO:
      * INPUT = "stdin"
      * OUTPUT = "stdout"
    The `stdin` argument is BytesIO contain compressed image data(PNG, JPG, TIFF, etc).

    See https://github.com/tesseract-ocr/tesseract/blob/main/doc/tesseract.1.asc
    for more information.
    """
    command = [TESSERACT_PATH] + arguments
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env or None,
        cwd=cwd or None,
        shell=True,
        startupinfo=STARTUPINFO,
    )
    image_data = None
    if stdin:
        # read from beginning
        stdin.seek(0)
        image_data = stdin.read()

    stdout, stderr = process.communicate(input=image_data)

    if process.returncode == 0:
        return stdout.decode("utf-8")
    return stderr.decode("utf-8")


def get_version() -> str:
    """get tesseract version"""

    arguments = ["--version"]
    tesseract_result = run_tesseract(arguments)
    pattern = r"tesseract (v\d+(?:\.\d+)+)"
    match = re.search(pattern, tesseract_result)
    if not match:
        raise ValueError("unable get version pattern")
    return match.group(1)


def get_installed_languages() -> List[str]:
    """get installed language(s) for OCR"""

    arguments = ["--list-langs"]
    tesseract_result = run_tesseract(arguments)
    lines = tesseract_result.splitlines()
    return list(lines[1:])


OCRLanguage = str
"""Language used for OCR"""


class LogLevel(StrEnum):
    ALL = "ALL"
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"
    OFF = "OFF"


class PageSegmentationMode(IntEnum):
    """Page segmentation modes (PSM)"""

    OSD_ONLY = 0
    """Orientation and script detection (OSD) only."""
    AUTO_OSD = 1
    """Automatic page segmentation with OSD."""
    AUTO_ONLY = 2
    """Automatic page segmentation, but no OSD, or OCR. (not implemented)"""
    AUTO = 3
    """Fully automatic page segmentation, but no OSD. (Default)"""
    SINGLE_COLUMN = 4
    """Assume a single column of text of variable sizes."""
    SINGLE_BLOCK_VERT_TEXT = 5
    """Assume a single uniform block of vertically aligned text."""
    SINGLE_BLOCK = 6
    """Assume a single uniform block of text."""
    SINGLE_LINE = 7
    """Treat the image as a single text line."""
    SINGLE_WORD = 8
    """Treat the image as a single word."""
    CIRCLE_WORD = 9
    """Treat the image as a single word in a circle."""
    SINGLE_CHAR = 10
    """Treat the image as a single character."""
    SPARSE_TEXT = 11
    """Sparse text. Find as much text as possible in no particular order."""
    SPARSE_TEXT_OSD = 12
    """Sparse text with OSD."""
    RAW_LINE = 13
    """Raw line. Treat the image as a single text line,
    bypassing hacks that are Tesseract-specific."""


class OCREngineMode(IntEnum):
    """OCR Engine modes (OEM)"""

    TESSERACT_ONLY = 0
    """Legacy engine only."""
    LSTM_ONLY = 1
    """Neural nets LSTM engine only."""
    TESSERACT_LSTM_COMBINED = 2
    """Legacy + LSTM engines."""
    DEFAULT = 3
    """Default, based on what is available."""


@dataclass
class TesseractOptions:
    """Tesseract Options"""

    tessdata_path: Optional[Path] = None
    """Location of tessdata path"""
    user_words_file: Optional[Path] = None
    """Location of user words file"""
    user_patterns_file: Optional[Path] = None
    """Location of user patterns file"""
    dpi: Optional[int] = None
    """DPI for input image"""
    log_level: Optional[LogLevel] = None
    """Logging level"""
    languages: Optional[List[OCRLanguage]] = None
    """Language(s) used for OCR"""
    config: Optional[Dict[str, str]] = None
    """Config variables"""
    page_segmentation_mode: Optional[PageSegmentationMode] = None
    """Page segmentation mode"""
    ocr_engine_mode: Optional[OCREngineMode] = None
    """OCR Engine mode"""

    def get_arguments(self) -> List[str]:
        arguments = []
        field_to_argument_map = {
            "tessdata_path": "--tessdata-dir",
            "user_words_file": "--user-words",
            "user_patterns_file": "--user-patterns",
            "dpi": "--dpi",
            "log_level": "--loglevel",
            "languages": "-l",
            "config": "-c",
            "page_segmentation_mode": "--psm",
            "ocr_engine_mode": "--oem",
        }
        for f in fields(self):
            name = f.name
            if value := getattr(self, name):
                if isinstance(value, Enum):
                    value = value.value

                elif name == "languages":
                    value = "+".join(value)

                elif name == "config":
                    value = " ".join([f"{k}={v}" for k, v in value.items()])

                arguments.extend([field_to_argument_map[name], str(value)])

        return arguments


def get_text(
    image: Union[Path, str, BytesIO],
    options: Optional[TesseractOptions] = None,
    env: Optional[Dict[str, Any]] = None,
    cwd: Optional[Path] = None,
) -> str:
    """get text from image"""

    inputbase = "stdin"
    outputbase = "stdout"
    if isinstance(image, (Path, str)):
        inputbase = str(image)

    arguments = [inputbase, outputbase]

    if options:
        arguments.extend(options.get_arguments())

    if isinstance(image, BytesIO):
        return run_tesseract(arguments, stdin=image)

    return run_tesseract(arguments)


def _box_to_dict(line: str) -> Dict[str, str]:
    keys = ("symbol", "left", "bottom", "right", "top", "page")
    values = line.strip()
    return dict(zip(keys, values))


def get_textbox(
    image: Union[Path, str, BytesIO],
    options: Optional[TesseractOptions] = None,
    env: Optional[Dict[str, Any]] = None,
    cwd: Optional[Path] = None,
) -> List[Dict[str, str]]:

    inputbase = "stdin"
    outputbase = "stdout"
    if isinstance(image, (Path, str)):
        inputbase = str(image)

    arguments = [inputbase, outputbase]

    if options:
        arguments.extend(options.get_arguments())

    arguments.append("makebox")

    if isinstance(image, BytesIO):
        tesseract_result = run_tesseract(arguments, stdin=image)
    else:
        tesseract_result = run_tesseract(arguments)

    lines = tesseract_result.splitlines()
    return [_box_to_dict(l) for l in lines[1:]]


def _tsv_to_dict(line: str) -> Dict[str, str]:
    keys = (
        "level",
        "page_num",
        "block_num",
        "par_num",
        "line_num",
        "word_num",
        "left",
        "top",
        "width",
        "height",
        "conf",
        "text",
    )
    values = line.split("\t")
    return dict(zip(keys, values))


def get_textdata(
    image: Union[Path, str, BytesIO],
    options: Optional[TesseractOptions] = None,
    env: Optional[Dict[str, Any]] = None,
    cwd: Optional[Path] = None,
) -> List[Dict[str, str]]:

    inputbase = "stdin"
    outputbase = "stdout"
    if isinstance(image, (Path, str)):
        inputbase = str(image)

    arguments = [inputbase, outputbase]

    if options:
        arguments.extend(options.get_arguments())

    arguments.append("tsv")

    if isinstance(image, BytesIO):
        tesseract_result = run_tesseract(arguments, stdin=image)
    else:
        tesseract_result = run_tesseract(arguments)

    lines = tesseract_result.splitlines()
    return [_tsv_to_dict(l) for l in lines[1:]]
