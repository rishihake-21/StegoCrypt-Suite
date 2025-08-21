import os
import cv2
import numpy as np
import struct
import hashlib


def _bytes_to_bits(data: bytes):
    # Vectorized conversion using numpy for speed
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits.astype(np.uint8)


def _bits_to_bytes(bits):
    # Vectorized conversion using numpy for speeda
    bits_np = np.asarray(list(bits), dtype=np.uint8)
    if bits_np.size == 0:
        return b""
    # pad to full byte
    pad = (-bits_np.size) % 8
    if pad:
        bits_np = np.pad(bits_np, (0, pad), constant_values=0)
    packed = np.packbits(bits_np)
    return packed.tobytes()


def _xor_with_password(data: bytes, password: str) -> bytes:
    if not password:
        return data
    pwd = password.encode("utf-8")
    result = bytearray(len(data))
    counter = 0
    pos = 0
    while pos < len(data):
        h = hashlib.sha256()
        h.update(pwd)
        h.update(struct.pack(">I", counter))
        block = h.digest()
        take = min(len(block), len(data) - pos)
        for i in range(take):
            result[pos + i] = data[pos + i] ^ block[i]
        pos += take
        counter += 1
    return bytes(result)


def _estimate_capacity_bits(cap) -> int:
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0 or width <= 0 or height <= 0:
        return 0
    return frame_count * width * height * 3


def _choose_writer(width: int, height: int, fps: float, out_path: str):
    # Prefer lossless/near-lossless AVI to preserve LSBs
    final_out = out_path
    base, ext = os.path.splitext(out_path)
    if ext.lower() != ".avi":
        final_out = base + ".avi"

    # Try FFV1 (lossless), then MJPG as fallback
    tried = []

    def try_codec(fourcc_code):
        writer = cv2.VideoWriter(final_out, cv2.VideoWriter_fourcc(*fourcc_code), fps if fps > 0 else 25.0, (width, height))
        return writer

    for code in ("FFV1", "HFYU", "LAGS", "MJPG"):
        w = try_codec(code)
        tried.append(code)
        if w.isOpened():
            return w, final_out, code
        w.release()

    # Fallback to mp4v if nothing else works (not recommended for LSB)
    w = cv2.VideoWriter(base + ".mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps if fps > 0 else 25.0, (width, height))
    return w, base + ".mp4", "mp4v"


def encode_text(video_path: str, message: str, out_path: str = "out/stego.avi", password: str = ""):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Unable to open video.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if not os.path.exists("out"):
        os.makedirs("out", exist_ok=True)

    message_bytes = message.encode("utf-8")
    encrypted_payload = _xor_with_password(message_bytes, password)
    header = struct.pack(">I", len(encrypted_payload))
    data_to_embed = header + encrypted_payload
    bits = _bytes_to_bits(data_to_embed)
    total_bits = int(bits.size)

    estimated_capacity = _estimate_capacity_bits(cap)
    if estimated_capacity and total_bits > estimated_capacity:
        print("❌ Message too large for the given video.")
        print(f"   Required bits: {total_bits}, capacity: {estimated_capacity}")
        cap.release()
        return

    out, final_out_path, codec = _choose_writer(width, height, fps, out_path)
    if not out.isOpened():
        cap.release()
        print("❌ Failed to open video writer.")
        return
    if codec in ("MJPG", "mp4v"):
        print("⚠️ Using a lossy codec (" + codec + ") may corrupt hidden bits. Prefer FFV1/HFYU/LAGS.")

    bit_index = 0
    wrote_any = False
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if bit_index < total_bits:
            flat = frame.reshape(-1)
            remaining = total_bits - bit_index
            count = min(flat.size, remaining)
            # Vectorized LSB write
            np.bitwise_and(flat[:count], 0xFE, out=flat[:count])
            np.bitwise_or(flat[:count], bits[bit_index:bit_index + count], out=flat[:count])
            bit_index += count
            frame = flat.reshape((height, width, 3))
            wrote_any = True

        out.write(frame)

    cap.release()
    out.release()

    if bit_index < total_bits:
        # Not enough frames/pixels to embed the full message
        try:
            if os.path.exists(final_out_path):
                os.remove(final_out_path)
        except Exception:
            pass
        missing = total_bits - bit_index
        print("❌ Video ended before message was fully encoded.")
        print(f"   Missing bits: {missing}")
        return

    if wrote_any:
        print(f"\n✅ Message successfully hidden in: {final_out_path}")
    else:
        print("❌ No frames written. Check input video.")


def decode_text(video_path: str, password: str = ""):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Unable to open video.")
        return

    # Collect bits vectorized for speed
    bits_collected = []

    # First, collect 32 bits for the header
    while True:
        if sum(len(a) for a in bits_collected) >= 32:
            break
        ret, frame = cap.read()
        if not ret:
            cap.release()
            print("❌ Video too short to contain header.")
            return
        lsbs = np.bitwise_and(frame.reshape(-1), 1)
        bits_collected.append(lsbs)

    all_bits = np.concatenate(bits_collected)
    header_bits = all_bits[:32]
    header_bytes = np.packbits(header_bits).tobytes()
    (payload_len,) = struct.unpack(">I", header_bytes)

    required_total = 32 + payload_len * 8
    # If we already have enough bits, slice; otherwise, keep reading
    while all_bits.size < required_total:
        ret, frame = cap.read()
        if not ret:
            cap.release()
            print("❌ Video ended before full payload could be read.")
            return
        lsbs = np.bitwise_and(frame.reshape(-1), 1)
        all_bits = np.concatenate([all_bits, lsbs])

    cap.release()

    payload_bits = all_bits[32:32 + payload_len * 8]
    payload_bytes = np.packbits(payload_bits).tobytes()
    decrypted = _xor_with_password(payload_bytes, password)

    try:
        message = decrypted.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback if wrong password or non-text payload
        message = decrypted.decode("utf-8", errors="replace")

    print("\n✅ Hidden message:")
    print(message)


def menu():
    while True:
        print("\n========= Video Steganography =========")
        print("1. Encode message into video")
        print("2. Decode message from video")
        print("3. Exit")

        choice = input("Choose an option (1-3): ").strip()

        if choice == '1':
            video = input("Enter path to cover video (e.g., cricket.mp4): ").strip()
            message = input("Enter your secret message: ").strip()
            password = input("Optional password (press Enter to skip): ").strip()
            out_path = input("Output path [default: out/stego.avi]: ").strip() or "out/stego.avi"
            if message:
                encode_text(video, message, out_path=out_path, password=password)
            else:
                print("❌ Empty message. Try again.")
        elif choice == '2':
            video = input("Enter path to stego video (e.g., out/stego.mp4): ").strip()
            password = input("Optional password (press Enter to skip): ").strip()
            decode_text(video, password=password)
        elif choice == '3':
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    menu()
