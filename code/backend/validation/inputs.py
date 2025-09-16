from .errors import ValidationError
import base64


def non_empty_string(value: str, name: str = "value") -> str:
    if value is None or len(value.strip()) == 0:
        raise ValidationError(f"{name} must not be empty")
    return value


def validate_base64(value: str, name: str = "base64") -> bytes:
    non_empty_string(value, name)
    try:
        return base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValidationError(f"Invalid {name}: not valid Base64") from exc


def safe_int(value: str, name: str = "integer") -> int:
    non_empty_string(value, name)
    try:
        return int(value)
    except Exception as exc:
        raise ValidationError(f"Invalid {name}: not an integer") from exc


