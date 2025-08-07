from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64, os

PRIVATE_KEY_FILE = "private_rsa.pem"
PUBLIC_KEY_FILE = "public_rsa.pem"

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
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
        print("No existing key pair found. Generating new...")
        generate_and_save_keys(password)
    
    with open(PRIVATE_KEY_FILE, 'rb') as f:
        private_key = RSA.import_key(f.read(), passphrase=password)
    with open(PUBLIC_KEY_FILE, 'rb') as f:
        public_key = RSA.import_key(f.read())
    return private_key, public_key

def encrypt_rsa(public_key, plaintext):
    cipher = PKCS1_OAEP.new(public_key)
    ciphertext = cipher.encrypt(plaintext.encode())
    return base64.b64encode(ciphertext).decode()

def decrypt_rsa(private_key, ciphertext_b64):
    cipher = PKCS1_OAEP.new(private_key)
    ciphertext = base64.b64decode(ciphertext_b64)
    return cipher.decrypt(ciphertext).decode()

def main():
    password = input("Enter password for RSA private key (press Enter to skip): ").strip()
    if password == "":
        password = None

    private_key, public_key = load_keys(password)

    while True:
        print("\n--- RSA MENU ---")
        print("1. Encrypt Text")
        print("2. Decrypt Text")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            text = input("Enter text to encrypt: ")
            encrypted = encrypt_rsa(public_key, text)
            print("Encrypted:", encrypted)
        elif choice == '2':
            encrypted = input("Enter encrypted text (Base64): ")
            try:
                decrypted = decrypt_rsa(private_key, encrypted)
                print("Decrypted:", decrypted)
            except:
                print("Invalid ciphertext or wrong key/password!")
        elif choice == '3':
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
