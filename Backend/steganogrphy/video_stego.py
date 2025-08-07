import cv2
import numpy as np

START_MARK = "STEGO_START"
END_MARK = "STEGO_END"

def text_to_bin(text):
    return ''.join(format(ord(c), '08b') for c in text)

def bin_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

def embed_binary(frame, data_bits):
    flat = frame.reshape(-1)
    flat[:len(data_bits)] = (flat[:len(data_bits)] & 254) | data_bits
    return flat.reshape(frame.shape)

def extract_binary(frame, bit_count):
    flat = frame.reshape(-1)
    bits = flat[:bit_count] & 1
    return ''.join(map(str, bits))

def encode_video(input_path, output_path, message, frame_number_to_hide=5):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise Exception("Could not open input video")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if frame_number_to_hide >= total_frames or frame_number_to_hide <= 0:
        raise Exception(f"Frame number must be between 1 and {total_frames-1}")

    # Choose stable codec
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        raise Exception("Could not create output video writer")

    # Prepare data
    full_msg = START_MARK + message + END_MARK
    msg_bits = np.array([int(b) for b in text_to_bin(full_msg)], dtype=np.uint8)

    frame_num_bits = np.array([int(b) for b in format(frame_number_to_hide, '016b')], dtype=np.uint8)

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx == 0:
            frame = embed_binary(frame, frame_num_bits)
        elif frame_idx == frame_number_to_hide:
            frame = embed_binary(frame, msg_bits)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    print(f"[i] Message embedded successfully in frame {frame_number_to_hide}")

def decode_video(stego_path):
    cap = cv2.VideoCapture(stego_path)
    if not cap.isOpened():
        raise Exception("Could not open stego video")

    # Extract frame index from frame 0
    ret, frame0 = cap.read()
    if not ret:
        raise Exception("Could not read frame 0")

    frame_num_bits = extract_binary(frame0, 16)
    target_frame = int(frame_num_bits, 2)

    # Jump to target frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, target_frame_img = cap.read()
    if not ret:
        raise Exception(f"Could not read frame {target_frame}")

    # Extract large data buffer (we cut after END_MARK)
    bits = extract_binary(target_frame_img, target_frame_img.size)
    message = bin_to_text(bits)

    start = message.find(START_MARK)
    end = message.find(END_MARK)
    if start == -1 or end == -1:
        print("[!] No valid message found")
        return

    secret = message[start + len(START_MARK):end]
    print("\nDecoded Message:\n>", secret)

def main():
    while True:
        print("\n VIDEO STEGANOGRAPHY MENU")
        print("1. Encode")
        print("2. Decode")
        print("3. Exit")
        choice = input("Choose (1/2/3): ")

        if choice == '1':
            input_path = input("Enter input video path: ")
            output_path = input("Enter output video path (e.g., stego.avi): ")
            message = input("Enter the message to hide: ")
            encode_video(input_path, output_path, message)
        elif choice == '2':
            stego_path = input("Enter stego video path: ")
            decode_video(stego_path)
        elif choice == '3':
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
