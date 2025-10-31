import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import logging
import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from appm.exceptions import NotAFileErr, NotFoundErr


def slugify(text: str) -> str:
    """Generate a slug from a text

    Used for generating project name and url slug

    https://developer.mozilla.org/en-US/docs/Glossary/Slug

    Example:
    - The Plant Accelerator -> the-plant-accelerator

    - APPN -> appn

    Args:
        text (str): source text

    Returns:
        str: slug
    """
    text = text.lower()
    # Replace non slug characters
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    # Replace spaces with hyphens
    text = re.sub(r"[\s\-]+", "-", text)
    return text.strip("-")


def to_flow_style(obj: Any) -> Any:
    """Recursively convert dict/list to ruamel structures with ALL lists using flow-style."""
    if isinstance(obj, Mapping):
        cm = CommentedMap()
        for k, v in obj.items():
            cm[k] = to_flow_style(v)
        return cm
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        cs = CommentedSeq()
        for item in obj:
            cs.append(to_flow_style(item))
        cs.fa.set_flow_style()
        return cs
    return obj


def validate_path(path: str | Path, is_file: bool = False) -> Path:
    """Verify that path describes an existing file/folder

    Args:
        path (str | Path): path to validate
        is_file (bool): whether path is a file. Defaults to False.

    Raises:
        NotFoundErr: path item doesn't exist
        NotAFileErr: path doesn't describe a file

    Returns:
        Path: validated path
    """
    _path = Path(path)
    if not _path.exists():
        raise NotFoundErr(f"File not found: {path!s}")
    if is_file and not _path.is_file():
        raise NotAFileErr(f"Not a file: {path!s}")
    return _path



def get_logger(name: str = None):
    # Check if a shared logger exists
    shared_logger_name = name
    if shared_logger_name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(shared_logger_name)
    else:
        # Create a local logger
        logger = logging.getLogger(name or __name__)
        logger.setLevel(logging.INFO)

        # Avoid adding handlers multiple times
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    return logger
    
