import cv2
import numpy as np

def encode_video(input_video, message, output_video="encoded_video.avi"):
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print("[!] Could not open input video.")
        return

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Prepare message
    message += '###'  # Delimiter
    bits = np.array([int(b) for ch in message for b in format(ord(ch), '08b')], dtype=np.uint8)

    # Capacity check
    max_bits = frame_count * width * height * 3
    if len(bits) > max_bits:
        print(f"[!] Message too large for this video. Max capacity = {max_bits//8} characters.")
        cap.release()
        out.release()
        return

    bit_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if bit_idx < len(bits):
            flat = frame.reshape(-1)
            bits_to_write = min(len(bits) - bit_idx, flat.size)
            # Modify only required pixels
            flat[:bits_to_write] = (flat[:bits_to_write] & 254) | bits[bit_idx:bit_idx+bits_to_write]
            bit_idx += bits_to_write
            frame = flat.reshape(frame.shape)

        out.write(frame)

    cap.release()
    out.release()
    print(f"[i] Message encoded into {output_video}")

def decode_video(encoded_video):
    cap = cv2.VideoCapture(encoded_video)
    if not cap.isOpened():
        print("[!] Could not open encoded video.")
        return

    bit_buffer = ""
    decoded = ""
    delimiter = "###"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        flat = frame.reshape(-1)
        # Extract bits and directly convert to characters when 8 bits are ready
        for bit in (flat & 1):
            bit_buffer += str(bit)
            if len(bit_buffer) == 8:
                decoded += chr(int(bit_buffer, 2))
                bit_buffer = ""
                if decoded.endswith(delimiter):
                    cap.release()
                    print("\nDecoded Message:")
                    print(">", decoded[:-3])
                    return

    cap.release()
    print("\nNo valid message found.")


def main_menu():
    while True:
        print("\n VIDEO STEGANOGRAPHY MENU")
        print("1. Encode Message into Video")
        print("2. Decode Message from Video")
        print("3. Exit")

        choice = input("Select an option (1-3): ")

        if choice == '1':
            input_video = input("Enter input video file (e.g., video.mp4): ").strip()
            message = input("Enter the message to hide: ")
            encode_video(input_video, message)
        elif choice == '2':
            encoded_video = input("Enter encoded video file name: ").strip()
            decode_video(encoded_video)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
