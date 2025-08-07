import cv2
import numpy as np

def text_to_bin(text):
    return ''.join(format(ord(c), '08b') for c in text)

def bin_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(c, 2)) for c in chars)

def embed_binary_data(frame, binary_data):
    idx = 0
    for row in frame:
        for pixel in row:
            for n in range(3):  # R, G, B
                if idx < len(binary_data):
                    pixel[n] = np.uint8((int(pixel[n]) & ~1) | int(binary_data[idx]))
                    idx += 1
            if idx >= len(binary_data):
                return frame
    return frame

def extract_binary_data(frame, num_bits):
    bits = ''
    idx = 0
    for row in frame:
        for pixel in row:
            for n in range(3):
                if idx < num_bits:
                    bits += str(pixel[n] & 1)
                    idx += 1
            if idx >= num_bits:
                return bits
    return bits

# ========== Encoder ==========

def encode_video(input_path, output_path, message, frame_number_to_hide):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise Exception(" Could not open input video")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if frame_number_to_hide >= total_frames or frame_number_to_hide <= 0:
        raise Exception(f" Frame number must be between 1 and {total_frames-1}")

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    START_MARK = "STEGO_START"
    END_MARK = "STEGO_END"
    binary_msg = text_to_bin(START_MARK + message + END_MARK)

    # Embed frame number in frame 0 (as 16-bit binary)
    frame_number_bin = format(frame_number_to_hide, '016b')

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx == 0:
            frame = embed_binary_data(frame, frame_number_bin)
        elif frame_idx == frame_number_to_hide:
            frame = embed_binary_data(frame, binary_msg)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    print(" Message embedded successfully in frame", frame_number_to_hide)

# ========== Decoder ==========

def decode_video(stego_path):
    cap = cv2.VideoCapture(stego_path)
    if not cap.isOpened():
        raise Exception(" Could not open stego video")

    # Step 1: Read frame 0 and extract frame number
    ret, frame0 = cap.read()
    if not ret:
        raise Exception(" Could not read frame 0")

    frame_number_bin = extract_binary_data(frame0, 16)
    frame_to_extract = int(frame_number_bin, 2)

    # Step 2: Jump to that frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_to_extract)
    ret, target_frame = cap.read()
    if not ret:
        raise Exception(f" Could not read frame {frame_to_extract}")

    # Step 3: Extract message from that frame
    binary_data = extract_binary_data(target_frame, 200000)  # read up to 100k bits
    message = bin_to_text(binary_data)

    if "STEGO_START" not in message or "STEGO_END" not in message:
        print("[DEBUG] Raw decoded text:\n", message)
        return " No valid message found."

    start = message.find("STEGO_START") + len("STEGO_START")
    end = message.find("STEGO_END")
    print("[DEBUG] Raw decoded text:\n", message)
    return message[start:end]

# ========== Menu (Frontend Friendly) ==========

def main():
    print("Video Steganography Tool")
    print("1. Encode")
    print("2. Decode")
    choice = input("Choose (1/2): ")

    if choice == '1':
        input_video = input("Enter input video path (e.g., video.mp4): ")
        output_video = input("Enter output video path (e.g., stego.avi): ")
        secret_message = input("Enter the message to hide: ")

        # Auto-pick a safe frame number (e.g., frame 5)
        frame_number = 5

        try:
            encode_video(input_video, output_video, secret_message, frame_number)
        except Exception as e:
            print(e)

    elif choice == '2':
        stego_video = input("Enter stego video path (e.g., stego.avi): ")
        try:
            message = decode_video(stego_video)
            print("\n🔓 Decoded Message:\n➤", message)
        except Exception as e:
            print(e)

    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
