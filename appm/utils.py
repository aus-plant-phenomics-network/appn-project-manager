import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import logging
import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

import time
import errno

from typing import Callable

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
    # text = text.lower()
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
    if not safe_exists_with_retry(_path, retries=4):
        raise NotFoundErr(f"File not found: {path!s}")
    if is_file and not _path.is_file():
        raise NotAFileErr(f"Not a file: {path!s}")
    return _path


def get_task_logger(name: str) -> logging.Logger:
    try:
        from celery.utils.log import get_task_logger as _gtl  # local import
        get_celery_logger: Callable[[str], logging.Logger] = _gtl  # type: ignore[assignment]
        return get_celery_logger(name)
    except Exception:
        return logging.getLogger(name)
        

TRANSIENT_ERRNOS = {
    errno.ENETDOWN,
    errno.ENETUNREACH,
    errno.EHOSTDOWN,
    errno.EHOSTUNREACH,
    errno.ESTALE,
    errno.EBUSY,
    errno.ETIMEDOUT,
}

def safe_exists_with_retry(path: Path, retries: int = 2) -> bool:
    attempt = 0
    while True:
        try:
            # return os.stat(path, follow_symlinks=follow_symlinks)
            return path.exists()
        except FileNotFoundError:
            return False
        except PermissionError:
            return False
        except OSError as e:
            if e.errno in TRANSIENT_ERRNOS and attempt < retries:
                shared_logger.error(f'APPM: utils:safe_exists_with_retry(): path:{path}; retries:{retries}; {e}')
                # jittered backoff (e.g., 200, 400, 600... ms)
                attempt += 1
                delay = (0.20 *  attempt) 
                time.sleep(delay)                
                continue
            shared_logger.error(f'APPM: utils:safe_exists_with_retry(): path:{path}; retries:{retries}; {e}')
            return False


