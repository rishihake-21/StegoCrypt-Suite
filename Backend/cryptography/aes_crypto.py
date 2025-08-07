from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib, base64

def get_key_from_password(password):
    return hashlib.sha256(password.encode()).digest()[:16]

def encrypt_aes(key, plaintext):
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt_aes(key, ciphertext_b64):
    data = base64.b64decode(ciphertext_b64)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

def main():
    password = input("Enter password/key (press Enter to generate random): ").strip()
    if password:
        key = get_key_from_password(password)
        print("Key derived from password.")
    else:
        key = get_random_bytes(16)
        print("Random key generated (Base64):", base64.b64encode(key).decode())
        print("Save this key to decrypt later.")

    while True:
        print("\n--- AES MENU ---")
        print("1. Encrypt Text")
        print("2. Decrypt Text")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            text = input("Enter text to encrypt: ")
            encrypted = encrypt_aes(key, text)
            print("Encrypted:", encrypted)
        elif choice == '2':
            encrypted = input("Enter encrypted text (Base64): ")
            try:
                decrypted = decrypt_aes(key, encrypted)
                print("Decrypted:", decrypted)
            except:
                print("Invalid ciphertext or wrong key/password!")
        elif choice == '3':
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
