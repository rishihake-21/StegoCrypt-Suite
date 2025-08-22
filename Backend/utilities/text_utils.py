"""Text processing utilities for steganography."""


def text_to_bin(text):
    """Convert text to binary string representation."""
    return ''.join(format(ord(c), '08b') for c in text)


def add_delimiter(msg):
    """Add delimiter to message for steganography boundary detection."""
    return msg + "*^*^*"
