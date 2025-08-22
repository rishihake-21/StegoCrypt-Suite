from .errors import CapacityError, MissingDependencyError


def ensure_ffmpeg_available():
    try:
        from pydub import AudioSegment  # noqa: F401
    except Exception as exc:
        raise MissingDependencyError("ffmpeg/ffprobe not available for audio processing") from exc


def image_capacity_bits(width: int, height: int) -> int:
    return width * height * 3


def ensure_image_capacity(required_bits: int, width: int, height: int):
    cap = image_capacity_bits(width, height)
    if required_bits > cap:
        raise CapacityError(f"Message too large: needs {required_bits} bits, capacity {cap} bits")


def text_capacity_bits(num_words: int) -> int:
    return num_words * 12


def ensure_text_capacity(required_bits: int, num_words: int):
    cap = text_capacity_bits(num_words)
    if required_bits > cap:
        raise CapacityError(f"Message too large for cover text: needs {required_bits} bits, capacity {cap} bits")


