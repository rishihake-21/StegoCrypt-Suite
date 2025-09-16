import os
import cv2
import numpy as np
import struct
import tempfile
from io import BytesIO

def _bytes_to_bits(data: bytes):
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits.astype(np.uint8)

def _bits_to_bytes(bits):
    bits_np = np.asarray(list(bits), dtype=np.uint8)
    if bits_np.size == 0:
        return b""
    pad = (-bits_np.size) % 8
    if pad:
        bits_np = np.pad(bits_np, (0, pad), constant_values=0)
    packed = np.packbits(bits_np)
    return packed.tobytes()

def _estimate_capacity_bits(cap) -> int:
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0 or width <= 0 or height <= 0:
        return 0
    return frame_count * width * height * 3

def _choose_writer(width: int, height: int, fps: float, out_path: str):
    final_out = out_path
    base, ext = os.path.splitext(out_path)
    if ext.lower() != ".avi":
        final_out = base + ".avi"

    tried = []
    for code in ("FFV1", "HFYU", "LAGS", "MJPG"):
        writer = cv2.VideoWriter(final_out, cv2.VideoWriter_fourcc(*code), fps if fps > 0 else 25.0, (width, height))
        if writer.isOpened():
            return writer, final_out, code
        writer.release()

    writer = cv2.VideoWriter(base + ".mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps if fps > 0 else 25.0, (width, height))
    return writer, base + ".mp4", "mp4v"

def encode_video(video_path: str, message: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Unable to open video.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    message_bytes = message.encode("utf-8")
    header = struct.pack(">I", len(message_bytes))
    data_to_embed = header + message_bytes
    bits = _bytes_to_bits(data_to_embed)
    total_bits = int(bits.size)

    estimated_capacity = _estimate_capacity_bits(cap)
    if estimated_capacity and total_bits > estimated_capacity:
        cap.release()
        raise ValueError(f"Message too large for the given video. Required bits: {total_bits}, capacity: {estimated_capacity}")

    with tempfile.NamedTemporaryFile(suffix=".avi", delete=False) as tmpfile:
        temp_video_path = tmpfile.name

    out, final_out_path, codec = _choose_writer(width, height, fps, temp_video_path)
    if not out.isOpened():
        cap.release()
        os.remove(temp_video_path)
        raise IOError("Failed to open video writer.")

    bit_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if bit_index < total_bits:
            flat = frame.reshape(-1)
            remaining = total_bits - bit_index
            count = min(flat.size, remaining)
            np.bitwise_and(flat[:count], 0xFE, out=flat[:count])
            np.bitwise_or(flat[:count], bits[bit_index:bit_index + count], out=flat[:count])
            bit_index += count
            frame = flat.reshape((height, width, 3))

        out.write(frame)

    cap.release()
    out.release()

    if bit_index < total_bits:
        os.remove(final_out_path)
        raise ValueError(f"Video ended before message was fully encoded. Missing bits: {total_bits - bit_index}")

    with open(final_out_path, "rb") as f:
        video_bytes = f.read()
    
    os.remove(final_out_path)
    return video_bytes

def decode_video(video_bytes: bytes):
    """Decodes a message from a video given as bytes."""
    # OpenCV's VideoCapture requires a file path, so we write the bytes to a temporary file.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".avi") as tmp:
        tmp.write(video_bytes)
        video_file_path = tmp.name

    cap = cv2.VideoCapture(video_file_path)
    if not cap.isOpened():
        os.remove(video_file_path)
        raise IOError("Unable to open video stream from bytes.")

    try:
        # --- Optimized Bit Extraction ---

        # 1. Read just enough of the video to get the 32-bit header.
        header_bits = np.empty(32, dtype=np.uint8)
        bits_read = 0
        lsbs = np.array([])
        
        while bits_read < 32:
            ret, frame = cap.read()
            if not ret:
                raise ValueError("Video is too short to contain a message header.")
            
            lsbs = np.bitwise_and(frame.ravel(), 1)
            
            needed = 32 - bits_read
            can_take = min(needed, lsbs.size)
            
            header_bits[bits_read : bits_read + can_take] = lsbs[:can_take]
            bits_read += can_take
        
        # We might have read more bits than needed for the header. Store the overflow.
        overflow_bits = lsbs[can_take:]

        # 2. Unpack the header to find the payload length.
        header_bytes = np.packbits(header_bits).tobytes()
        (payload_len_bytes,) = struct.unpack(">I", header_bytes)
        payload_len_bits = payload_len_bytes * 8

        # 3. Pre-allocate a NumPy array for all the payload bits.
        payload_bits = np.empty(payload_len_bits, dtype=np.uint8)
        payload_bits_idx = 0

        # 4. Start by filling with any overflow bits from the header read.
        if overflow_bits.size > 0:
            can_take = min(overflow_bits.size, payload_len_bits)
            payload_bits[payload_bits_idx : payload_bits_idx + can_take] = overflow_bits[:can_take]
            payload_bits_idx += can_take

        # 5. Read subsequent frames to fill the rest of the payload array.
        while payload_bits_idx < payload_len_bits:
            ret, frame = cap.read()
            if not ret:
                raise ValueError("Video ended before the full message could be extracted.")
            
            lsbs = np.bitwise_and(frame.ravel(), 1)
            
            needed = payload_len_bits - payload_bits_idx
            can_take = min(needed, lsbs.size)
            
            payload_bits[payload_bits_idx : payload_bits_idx + can_take] = lsbs[:can_take]
            payload_bits_idx += can_take

        # 6. Convert the collected bits back into a message.
        payload_bytes = np.packbits(payload_bits).tobytes()
        message = payload_bytes.decode("utf-8", errors="replace")
        
        return message

    finally:
        # 7. Clean up resources.
        cap.release()
        os.remove(video_file_path)
