from PIL import Image
import utility as ut

def encode_image(image_path, output_path, secret_message):
    img = Image.open(image_path)

    if img.format != "PNG":
        img.save(image_path,"PNG")

    if img.mode != 'RGB':
        img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size

    binary_data = ut.text_to_bin(ut.add_demiliter(secret_message) ) # Delimiter
    data_len = len(binary_data)
    data_index = 0

    data_index = 0
    for y in range(height):
        for x in range(width):
            if data_index >= data_len:
                break
            r, g, b = pixels[x, y]
            if data_index < data_len:
                r = (r & ~1) | int(binary_data[data_index])
                data_index += 1
            if data_index < data_len:
                g = (g & ~1) | int(binary_data[data_index])
                data_index += 1
            if data_index < data_len:
                b = (b & ~1) | int(binary_data[data_index])
                data_index += 1
            pixels[x, y] = (r, g, b)
        if data_index >= data_len:
            break

    img.save(output_path, "PNG")
    print(f"Encoding complete. Saved stego image as: {output_path}")

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
                    print("Message not found. Possibly not encoded.")
                    return None

                if decoded_msg.endswith(stop_flag):
                    print("Decoded Message:", decoded_msg[:-len(stop_flag)])
                    return decoded_msg[:-len(stop_flag)]

    print("No hidden message found.")
    return None

def main():

    print("IMAGE STEGANOGRAPHY MENU")
    print("1. Encode")
    print("2. Decode")
    choice = input("Choose (1/2): ")

    if choice == '1':
        input_image = input("Enter input image path: ")
        output_image = input("Enter output image path: ")
        secret_message = input("Enter the message to hide: ")
        encode_image(input_image, output_image, secret_message)

    elif choice == '2':
        encoded_image = input("Enter encoded image path (e.g., encoded.png): ")
        decode_image(encoded_image)

    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
