from .api import (
    get_text,
    get_textbox,
    get_textdata,
    get_version,
    get_installed_languages,
    run_tesseract,
    TesseractOptions,
    LogLevel,
    OCRLanguage,
    PageSegmentationMode,
    OCREngineMode,
)

__all__ = [
    "get_text",
    "get_textbox",
    "get_textdata",
    "get_version",
    "get_installed_languages",
    "run_tesseract",
    "TesseractOptions",
    "LogLevel",
    "OCRLanguage",
    "PageSegmentationMode",
    "OCREngineMode",
]

__version__ = "0.1.0"
