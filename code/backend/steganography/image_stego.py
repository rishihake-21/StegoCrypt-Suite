from io import BytesIO
from PIL import Image
from utilities.text_utils import text_to_bin, add_delimiter
from validation.inputs import non_empty_string
from validation.media import ensure_image_capacity

def encode_image(image_path, secret_message):
    img = Image.open(image_path)

    if img.mode != 'RGB':
        img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size

    non_empty_string(secret_message, "secret message")

    binary_data = text_to_bin(add_delimiter(secret_message))
    data_len = len(binary_data)
    ensure_image_capacity(data_len, width, height)

    data_index = 0
    for y in range(height):
        for x in range(width):
            if data_index >= data_len:
                break
            r, g, b = pixels[x, y]
            if data_index < data_len:
                r = (r & ~1) | int(binary_data[data_index]); data_index += 1
            if data_index < data_len:
                g = (g & ~1) | int(binary_data[data_index]); data_index += 1
            if data_index < data_len:
                b = (b & ~1) | int(binary_data[data_index]); data_index += 1
            pixels[x, y] = (r, g, b)
        if data_index >= data_len:
            break

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()  # return PNG bytes


def decode_image(image_path):
    img = Image.open(image_path)
    binary_data = ""
    decoded_msg = ""
    stop_flag = "*^*^*"  # Text-based delimiter
    MAX_CHARS = 1000

    for y in range(img.height):
        for x in range(img.width):
            r, g, b = img.getpixel((x, y))
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)

            while len(binary_data) >= 8:
                byte = binary_data[:8]
                binary_data = binary_data[8:]
                char = chr(int(byte, 2))
                decoded_msg += char

                if len(decoded_msg) > MAX_CHARS:
                    return None

                if decoded_msg.endswith(stop_flag):
                    return decoded_msg[:-len(stop_flag)]
    return None

def main():

    print("IMAGE STEGANOGRAPHY MENU")
    print("1. Encode")
    print("2. Decode")
    choice = input("Choose (1/2): ")

    if choice == '1':
        input_image = input("Enter input image path: ")
        output_image_path = input("Enter output image path: ")
        secret_message = input("Enter the message to hide: ")
        
        # Get the encoded image bytes
        encoded_bytes = encode_image(input_image, secret_message)
        
        # Save the bytes to the specified output file
        with open(output_image_path, "wb") as f:
            f.write(encoded_bytes)
        print(f"Image saved to {output_image_path}")

    elif choice == '2':
        encoded_image = input("Enter encoded image path (e.g., encoded.png): ")
        decode_image(encoded_image)

    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
