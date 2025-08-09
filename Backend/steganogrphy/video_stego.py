import cv2
import numpy as np

def text_to_bits(text):
    """Convert text to a binary string."""
    return ''.join(format(ord(c), '08b') for c in text)

def bits_to_text(bits):
    """Convert binary string back to text."""
    chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
    return ''.join(chars)

def encode_image(input_path, output_path, message):
    """Encode a message into an image."""
    # Read the input image
    frame = cv2.imread(input_path)
    if frame is None:
        print("[!] Error reading image.")
        return

    # Convert message to bits with an end marker
    message += "<<<EOF>>>"
    bits = text_to_bits(message)
    flat = frame.flatten()

    # Check if message fits in the image
    if len(bits) > len(flat):
        print("[!] Message too long.")
        return

    # Define a uint8 mask to clear the LSB (254 = 0b11111110)
    mask = np.uint8(254)

    # Embed the message in the LSB of each pixel
    for i in range(len(bits)):
        flat[i] = (flat[i] & mask) | np.uint8(int(bits[i]))

    # Reshape and save the modified image
    frame = flat.reshape(frame.shape)
    cv2.imwrite(output_path, frame)
    print("[+] Image saved to:", output_path)

def decode_image(stego_path):
    """Decode a message from an image."""
    # Read the encoded image
    frame = cv2.imread(stego_path)
    if frame is None:
        print("[!] Error reading image.")
        return

    # Extract LSBs from all pixels
    flat = frame.flatten()
    bits = ''.join([str(b & 1) for b in flat])
    decoded = bits_to_text(bits)

    # Extract the message up to the end marker
    if "<<<EOF>>>" in decoded:
        message = decoded.split("<<<EOF>>>")[0]
        print("[+] Hidden message:", message)
    else:
        print("[!] No hidden message found.")

# Run the test
if __name__ == "__main__":
    encode_image("test.jpg", "stego.png", "secret message")
    decode_image("stego.png")