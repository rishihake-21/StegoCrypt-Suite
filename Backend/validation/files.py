from pathlib import Path
from .errors import ValidationError


def path_exists(path_str: str, name: str = "path") -> Path:
    p = Path(path_str)
    if not p.exists():
        raise ValidationError(f"{name} does not exist: {p}")
    return p


def is_readable(path: Path, name: str = "file") -> Path:
    if not path.is_file():
        raise ValidationError(f"{name} is not a file: {path}")
    try:
        with path.open("rb"):
            pass
    except Exception as exc:
        raise ValidationError(f"{name} is not readable: {path}") from exc
    return path


def has_ext(path: Path, *exts: str, name: str = "file") -> Path:
    if not any(str(path).lower().endswith(e.lower()) for e in exts):
        raise ValidationError(f"{name} must have one of extensions {exts}: {path}")
    return path


