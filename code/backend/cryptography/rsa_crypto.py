import os, sys
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Ensure Backend is on sys.path for local script execution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from validation.inputs import non_empty_string

# Store keys in user's home directory for better security
KEY_DIR = Path.home() / ".stegocrypt_keys"
KEY_DIR.mkdir(exist_ok=True)

PRIVATE_KEY_FILE = KEY_DIR / "private_rsa.pem"
PUBLIC_KEY_FILE = KEY_DIR / "public_rsa.pem"

def generate_and_save_keys(password=None):
    key = RSA.generate(2048)
    private_key = key.export_key(passphrase=password, pkcs=8,protection="scryptAndAES128-CBC" if password else None)
    with open(PRIVATE_KEY_FILE, 'wb') as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open(PUBLIC_KEY_FILE, 'wb') as f:
        f.write(public_key)
    print("New RSA key pair generated and saved.")

def load_keys(password=None):
    try:
        if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
            print("No existing key pair found. Generating new...")
            generate_and_save_keys(password)
        
        with open(PRIVATE_KEY_FILE, 'rb') as f:
            private_key = RSA.import_key(f.read(), passphrase=password)
        with open(PUBLIC_KEY_FILE, 'rb') as f:
            public_key = RSA.import_key(f.read())
        return private_key, public_key
    except Exception as e:
        print(f"❌ Error loading keys: {e}")
        print("This might be due to wrong password or corrupted key files.")
        return None, None

def encrypt_rsa(public_key, plaintext):
    """Encrypt plaintext and return raw bytes"""
    cipher = PKCS1_OAEP.new(public_key)
    ciphertext = cipher.encrypt(plaintext.encode())
    return ciphertext

def decrypt_rsa(private_key, ciphertext):
    """Decrypt ciphertext bytes and return plaintext string"""
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(ciphertext).decode()

def main():
    try:
        password = input("Enter password for RSA private key: ").strip()
        if password == "":
            password = None

        private_key, public_key = load_keys(password)
        
        if private_key is None or public_key is None:
            print("❌ Failed to load keys. Exiting.")
            return

        while True:
            print("\n--- RSA MENU ---")
            print("1. Encrypt Text")
            print("2. Decrypt Text")
            print("3. Exit")
            choice = input("Enter choice: ")

            if choice == '1':
                text = input("Enter text to encrypt: ").strip()
                try:
                    non_empty_string(text, "text")
                    encrypted = encrypt_rsa(public_key, text)
                    print("✅ Encrypted (raw bytes):", encrypted.hex())
                    print("   Length:", len(encrypted), "bytes")
                except Exception as e:
                    print(f"❌ Encryption failed: {e}")
            elif choice == '2':
                encrypted_hex = input("Enter encrypted text (hex): ").strip()
                try:
                    encrypted = bytes.fromhex(encrypted_hex)
                    decrypted = decrypt_rsa(private_key, encrypted)
                    print("✅ Decrypted:", decrypted)
                except Exception as e:
                    print(f"❌ Decryption failed: {e}")
                    print("This might be due to wrong password, corrupted data, or invalid input.")
            elif choice == '3':
                print("👋 Exiting.")
                break
            else:
                print("❌ Invalid choice! Please enter 1, 2, or 3.")
    except KeyboardInterrupt:
        print("\n\n👋 Exiting.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
