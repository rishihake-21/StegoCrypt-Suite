# Enhanced X25519 File Encryption System
# A secure file encryption module using X25519 KEM + AES-GCM

import os
import json
import hmac
import hashlib
import struct
import secrets
import sys
import base64
import ctypes
import getpass
from typing import Tuple, Optional, Callable, List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path

# Required dependencies
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install cryptography")
    sys.exit(1)

# Constants
MAGIC_BYTES = b'X25F'  # Updated to reflect X25519
CURRENT_VERSION = 3
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4MB
HKDF_INFO = b'x25519-file-encryption:v3'
SALT_SIZE = 16
NONCE_BASE_SIZE = 12
KEY_SIZE = 32
MAC_KEY_SIZE = 32

# Enhanced Scrypt parameters
SCRYPT_LENGTH = 32
SCRYPT_N = 16384  # 2^14
SCRYPT_R = 8
SCRYPT_P = 1

# Required metadata keys
REQUIRED_METADATA_KEYS = {
    'version', 'kem_algo', 'kem_ciphertext', 'hkdf_salt', 'nonce_base',
    'chunk_size', 'aead_algo', 'original_size', 'hmac', 'kdf_algo', 'hkdf_info'
}


class SecureBuffer:
    """Secure buffer that automatically wipes memory on cleanup"""
    
    def __init__(self, size: int):
        self._buffer = bytearray(size)
        self._size = size
    
    @classmethod
    def from_bytes(cls, data: bytes):
        """Create secure buffer from existing bytes"""
        buf = cls(len(data))
        buf._buffer[:] = data
        return buf
    
    def __len__(self):
        return self._size
    
    def __getitem__(self, key):
        return self._buffer[key]
    
    def __setitem__(self, key, value):
        self._buffer[key] = value
    
    def to_bytes(self) -> bytes:
        """Convert to bytes (creates a copy)"""
        return bytes(self._buffer)
    
    def wipe(self):
        """Securely wipe the buffer contents"""
        if self._buffer:
            try:
                ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(self._buffer)), 0, len(self._buffer))
            except:
                for i in range(len(self._buffer)):
                    self._buffer[i] = 0
    
    def __del__(self):
        self.wipe()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wipe()


def secure_wipe(buffer):
    """Securely wipe a mutable buffer"""
    if isinstance(buffer, bytearray):
        try:
            ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(buffer)), 0, len(buffer))
        except:
            for i in range(len(buffer)):
                buffer[i] = 0
    elif hasattr(buffer, 'wipe'):
        buffer.wipe()


class X25519KEM:
    """X25519 Key Encapsulation Mechanism"""
    
    def __init__(self):
        self.key_size = 32
        self.ciphertext_size = 32  # Just the ephemeral public key
        
    def generate_keypair(self):
        """Generate X25519 keypair"""
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return public_bytes, private_bytes
    
    def encap_secret(self, public_key_bytes):
        """Encapsulate secret using X25519"""
        ephemeral_private = x25519.X25519PrivateKey.generate()
        ephemeral_public = ephemeral_private.public_key()
        
        public_key = x25519.X25519PublicKey.from_public_bytes(public_key_bytes)
        shared_key = ephemeral_private.exchange(public_key)
        
        ephemeral_public_bytes = ephemeral_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return ephemeral_public_bytes, shared_key
    
    def decap_secret(self, ciphertext, private_key_bytes):
        """Decapsulate secret using X25519"""
        ephemeral_public_bytes = ciphertext
        
        private_key = x25519.X25519PrivateKey.from_private_bytes(private_key_bytes)
        ephemeral_public = x25519.X25519PublicKey.from_public_bytes(ephemeral_public_bytes)
        
        shared_key = private_key.exchange(ephemeral_public)
        return shared_key


class ShamirSecretSharing:
    """Simple Shamir's Secret Sharing implementation"""
    
    PRIME = 2**127 - 1  # Mersenne prime
    
    @staticmethod
    def _eval_poly(coeffs: List[int], x: int, prime: int) -> int:
        """Evaluate polynomial at x using Horner's method"""
        result = 0
        for coeff in reversed(coeffs):
            result = (result * x + coeff) % prime
        return result
    
    @staticmethod
    def _lagrange_interpolate(points: List[Tuple[int, int]], prime: int) -> int:
        """Lagrange interpolation to find f(0)"""
        def mod_inverse(a: int, m: int) -> int:
            return pow(a, m - 2, m)
        
        result = 0
        for i, (xi, yi) in enumerate(points):
            numerator = yi
            denominator = 1
            
            for j, (xj, _) in enumerate(points):
                if i != j:
                    numerator = (numerator * (-xj)) % prime
                    denominator = (denominator * (xi - xj)) % prime
            
            result = (result + numerator * mod_inverse(denominator, prime)) % prime
        
        return result
    
    @classmethod
    def split_secret(cls, secret: bytes, threshold: int, shares: int) -> List[bytes]:
        """Split secret into shares with given threshold"""
        if threshold > shares or threshold < 2:
            raise ValueError("Invalid threshold or share count")
        
        secret_int = int.from_bytes(secret, 'big')
        if secret_int >= cls.PRIME:
            raise ValueError("Secret too large for field")
        
        coeffs = [secret_int] + [secrets.randbelow(cls.PRIME) for _ in range(threshold - 1)]
        
        share_list = []
        for i in range(1, shares + 1):
            y = cls._eval_poly(coeffs, i, cls.PRIME)
            share_data = {
                'x': i,
                'y': y,
                'threshold': threshold,
                'secret_len': len(secret)
            }
            share_json = json.dumps(share_data).encode('utf-8')
            share_list.append(base64.b64encode(share_json))
        
        return share_list
    
    @classmethod
    def reconstruct_secret(cls, shares: List[bytes]) -> bytes:
        """Reconstruct secret from shares"""
        if len(shares) < 2:
            raise ValueError("Need at least 2 shares")
        
        points = []
        threshold = None
        secret_len = None
        
        for share in shares:
            share_data = json.loads(base64.b64decode(share).decode('utf-8'))
            if threshold is None:
                threshold = share_data['threshold']
                secret_len = share_data['secret_len']
            elif threshold != share_data['threshold']:
                raise ValueError("Threshold mismatch in shares")
            
            points.append((share_data['x'], share_data['y']))
        
        if len(points) < threshold:
            raise ValueError(f"Need at least {threshold} shares")
        
        points = points[:threshold]
        secret_int = cls._lagrange_interpolate(points, cls.PRIME)
        secret_bytes = secret_int.to_bytes(secret_len, 'big')
        
        return secret_bytes


class X25519FileEncryption:
    """File Encryption using X25519 KEM + AES-GCM"""
    
    def __init__(self):
        self.kem = X25519KEM()
        self.kem_algo = "X25519-KEM"
    
    def generate_keypair(self) -> Tuple[bytes, SecureBuffer, str]:
        """Generate X25519 keypair"""
        public_key, private_key_bytes = self.kem.generate_keypair()
        private_key = SecureBuffer.from_bytes(private_key_bytes)
        secure_wipe(bytearray(private_key_bytes))
        
        fingerprint = hashlib.sha256(public_key).hexdigest()[:16]
        return public_key, private_key, fingerprint
    
    def _derive_keys(self, shared_secret: bytes, salt: bytes) -> Tuple[SecureBuffer, SecureBuffer]:
        """Derive encryption and MAC keys"""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE + MAC_KEY_SIZE,
            salt=salt,
            info=HKDF_INFO,
            backend=default_backend()
        )
        
        derived = hkdf.derive(shared_secret)
        enc_key = SecureBuffer.from_bytes(derived[:KEY_SIZE])
        mac_key = SecureBuffer.from_bytes(derived[KEY_SIZE:])
        
        secure_wipe(bytearray(derived))
        return enc_key, mac_key
    
    def encrypt_file(self, input_path: str, output_path: str, public_key: bytes,
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """Encrypt file"""
        with open(input_path, 'rb') as f:
            data = f.read()
        
        if progress_callback:
            progress_callback(0, len(data))
        
        # Generate secrets
        kem_ciphertext, shared_bytes = self.kem.encap_secret(public_key)
        shared_secret = SecureBuffer.from_bytes(shared_bytes)
        secure_wipe(bytearray(shared_bytes))
        
        salt = secrets.token_bytes(SALT_SIZE)
        nonce_base = secrets.token_bytes(NONCE_BASE_SIZE)
        
        try:
            with shared_secret:
                enc_key, mac_key = self._derive_keys(shared_secret.to_bytes(), salt)
            
            with enc_key, mac_key:
                cipher = AESGCM(enc_key.to_bytes())
                
                # Create metadata
                metadata = {
                    "version": CURRENT_VERSION,
                    "kem_algo": self.kem_algo,
                    "kem_ciphertext": base64.b64encode(kem_ciphertext).decode('ascii'),
                    "hkdf_salt": base64.b64encode(salt).decode('ascii'),
                    "nonce_base": base64.b64encode(nonce_base).decode('ascii'),
                    "chunk_size": DEFAULT_CHUNK_SIZE,
                    "aead_algo": "AES-256-GCM",
                    "kdf_algo": "HKDF-SHA256",
                    "hkdf_info": base64.b64encode(HKDF_INFO).decode('ascii'),
                    "original_size": len(data),
                    "pub_fingerprint": hashlib.sha256(public_key).hexdigest()[:16],
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "hmac": ""  # Placeholder
                }
                
                # Encrypt data
                nonce = nonce_base + b'\x00\x00\x00\x00'
                ciphertext = cipher.encrypt(nonce, data, None)
                
                # Calculate HMAC
                hmac_ctx = hmac.new(mac_key.to_bytes(), digestmod=hashlib.sha256)
                hmac_ctx.update(ciphertext)
                final_hmac = hmac_ctx.digest()
                metadata["hmac"] = base64.b64encode(final_hmac).decode('ascii')
                
                # Serialize metadata
                metadata_json = json.dumps(metadata, sort_keys=True).encode('utf-8')
                
                # Write encrypted file
                with open(output_path, 'wb') as f:
                    f.write(MAGIC_BYTES)
                    f.write(struct.pack('>I', len(metadata_json)))
                    f.write(metadata_json)
                    f.write(ciphertext)
                
                if progress_callback:
                    progress_callback(len(data), len(data))
                
                return hashlib.sha256(public_key).hexdigest()[:16]
        
        finally:
            secure_wipe(bytearray(salt))
            secure_wipe(bytearray(nonce_base))
    
    def decrypt_file(self, input_path: str, output_path: str, private_key: SecureBuffer,
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Decrypt file"""
        with open(input_path, 'rb') as f:
            # Read magic bytes
            magic = f.read(4)
            if magic != MAGIC_BYTES:
                raise ValueError("Invalid file format")
            
            # Read metadata
            metadata_len = struct.unpack('>I', f.read(4))[0]
            metadata_json = f.read(metadata_len)
            metadata = json.loads(metadata_json.decode('utf-8'))
            
            # Extract parameters
            kem_ciphertext = base64.b64decode(metadata["kem_ciphertext"])
            salt = base64.b64decode(metadata["hkdf_salt"])
            nonce_base = base64.b64decode(metadata["nonce_base"])
            expected_hmac = base64.b64decode(metadata["hmac"])
            
            # Read ciphertext
            ciphertext = f.read()
        
        if progress_callback:
            progress_callback(0, len(ciphertext))
        
        # Decapsulate shared secret
        with private_key:
            shared_bytes = self.kem.decap_secret(kem_ciphertext, private_key.to_bytes())
            shared_secret = SecureBuffer.from_bytes(shared_bytes)
            secure_wipe(bytearray(shared_bytes))
        
        with shared_secret:
            enc_key, mac_key = self._derive_keys(shared_secret.to_bytes(), salt)
        
        with enc_key, mac_key:
            # Verify HMAC
            hmac_ctx = hmac.new(mac_key.to_bytes(), digestmod=hashlib.sha256)
            hmac_ctx.update(ciphertext)
            computed_hmac = hmac_ctx.digest()
            
            if not hmac.compare_digest(computed_hmac, expected_hmac):
                raise ValueError("HMAC verification failed - data may be corrupted")
            
            # Decrypt
            cipher = AESGCM(enc_key.to_bytes())
            nonce = nonce_base + b'\x00\x00\x00\x00'
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            if progress_callback:
                progress_callback(len(ciphertext), len(ciphertext))
            
            return True
    
    def protect_private_key(self, private_key: SecureBuffer, password: str) -> bytes:
        """Protect private key with password using Scrypt"""
        salt = secrets.token_bytes(16)
        
        try:
            kdf = Scrypt(
                length=32,
                salt=salt,
                n=SCRYPT_N,
                r=SCRYPT_R,
                p=SCRYPT_P,
                backend=default_backend()
            )
            derived_key = kdf.derive(password.encode('utf-8'))
            
            with SecureBuffer.from_bytes(derived_key) as key_buf:
                nonce = secrets.token_bytes(12)
                cipher = AESGCM(key_buf.to_bytes())
                ciphertext = cipher.encrypt(nonce, private_key.to_bytes(), None)
                
                key_blob = {
                    "version": CURRENT_VERSION,
                    "kdf": "scrypt",
                    "kdf_params": {
                        "n": SCRYPT_N,
                        "r": SCRYPT_R,
                        "p": SCRYPT_P,
                        "length": 32
                    },
                    "salt": base64.b64encode(salt).decode('ascii'),
                    "nonce": base64.b64encode(nonce).decode('ascii'),
                    "ciphertext": base64.b64encode(ciphertext).decode('ascii'),
                    "kem_algo": self.kem_algo
                }
                
                return json.dumps(key_blob, sort_keys=True).encode('utf-8')
        
        finally:
            if 'derived_key' in locals():
                secure_wipe(bytearray(derived_key))
    
    def unprotect_private_key(self, key_blob: bytes, password: str) -> SecureBuffer:
        """Unprotect private key with password"""
        try:
            blob_data = json.loads(key_blob.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Invalid key blob format")
        
        if blob_data.get("kdf") != "scrypt":
            raise ValueError("Unsupported KDF")
        
        params = blob_data["kdf_params"]
        salt = base64.b64decode(blob_data["salt"])
        nonce = base64.b64decode(blob_data["nonce"])
        ciphertext = base64.b64decode(blob_data["ciphertext"])
        
        try:
            kdf = Scrypt(
                length=params["length"],
                salt=salt,
                n=params["n"],
                r=params["r"],
                p=params["p"],
                backend=default_backend()
            )
            derived_key = kdf.derive(password.encode('utf-8'))
            
            with SecureBuffer.from_bytes(derived_key) as key_buf:
                cipher = AESGCM(key_buf.to_bytes())
                private_key_bytes = cipher.decrypt(nonce, ciphertext, None)
                return SecureBuffer.from_bytes(private_key_bytes)
        
        except Exception as e:
            if "verification failed" in str(e).lower():
                raise ValueError("Invalid password")
            raise ValueError(f"Key unprotection failed: {e}")
        
        finally:
            if 'derived_key' in locals():
                secure_wipe(bytearray(derived_key))
    
    def split_key_with_sss(self, private_key: SecureBuffer, password: str, 
                          threshold: int, shares: int) -> List[bytes]:
        """Split private key using Shamir's Secret Sharing"""
        encrypted_key = self.protect_private_key(private_key, password)
        return ShamirSecretSharing.split_secret(encrypted_key, threshold, shares)
    
    def reconstruct_key_from_sss(self, shares: List[bytes], password: str) -> SecureBuffer:
        """Reconstruct private key from SSS shares"""
        encrypted_key = ShamirSecretSharing.reconstruct_secret(shares)
        return self.unprotect_private_key(encrypted_key, password)
    
    @staticmethod
    def read_file_metadata(file_path: str) -> Dict[str, Any]:
        """Read metadata from encrypted file"""
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            if magic != MAGIC_BYTES:
                raise ValueError("Invalid file format")
            
            metadata_len = struct.unpack('>I', f.read(4))[0]
            metadata_json = f.read(metadata_len)
            return json.loads(metadata_json.decode('utf-8'))


class X25519CryptoMenu:
    """Menu system for X25519 file encryption"""
    
    def __init__(self):
        self.crypto = X25519FileEncryption()
        self.public_key = None
        self.private_key = None
        self.fingerprint = None
    
    def display_banner(self):
        """Display application banner"""
        print("=" * 60)
        print("X25519 File Encryption System")
        print("Secure file encryption with X25519 KEM + AES-GCM")
        print("=" * 60)
        print()
    
    def display_menu(self):
        """Display main menu options"""
        print("\nMain Menu:")
        print("1. Generate keypair")
        print("2. Load keypair")
        print("3. Save keypair")
        print("4. Encrypt file")
        print("5. Decrypt file")
        print("6. View file metadata")
        print("7. Protect private key")
        print("8. Secret sharing")
        print("9. Show current key info")
        print("0. Exit")
        print("-" * 40)
    
    def get_menu_choice(self) -> int:
        """Get user menu choice"""
        try:
            return int(input("Enter choice (0-9): ").strip())
        except ValueError:
            return -1
    
    def progress_display(self, current: int, total: int):
        """Progress callback for operations"""
        if total > 0:
            percent = (current * 100) // total
            print(f"\rProgress: {percent}%", end='', flush=True)
        if current >= total:
            print()
    
    def generate_keypair(self):
        """Generate new X25519 keypair"""
        print("\nGenerating X25519 keypair...")
        try:
            self.public_key, self.private_key, self.fingerprint = self.crypto.generate_keypair()
            print(f"Success! Keypair generated")
            print(f"Fingerprint: {self.fingerprint}")
        except Exception as e:
            print(f"Error generating keypair: {e}")
    
    def load_keypair(self):
        """Load keypair from files"""
        try:
            pub_file = input("Public key file path: ").strip()
            priv_file = input("Private key file path: ").strip()
            
            if not os.path.exists(pub_file):
                print(f"Public key file not found: {pub_file}")
                return
            
            if not os.path.exists(priv_file):
                print(f"Private key file not found: {priv_file}")
                return
            
            with open(pub_file, 'rb') as f:
                self.public_key = f.read()
            
            with open(priv_file, 'rb') as f:
                private_key_data = f.read()
            
            # Check if protected
            try:
                json.loads(private_key_data.decode('utf-8'))
                password = getpass.getpass("Private key password: ")
                self.private_key = self.crypto.unprotect_private_key(private_key_data, password)
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.private_key = SecureBuffer.from_bytes(private_key_data)
            
            self.fingerprint = hashlib.sha256(self.public_key).hexdigest()[:16]
            print(f"Keypair loaded successfully! Fingerprint: {self.fingerprint}")
            
        except Exception as e:
            print(f"Error loading keypair: {e}")
    
    def save_keypair(self):
        """Save keypair to files"""
        if not self.public_key or not self.private_key:
            print("No keypair available. Generate or load first.")
            return
        
        try:
            pub_file = input("Public key save path: ").strip()
            priv_file = input("Private key save path: ").strip()
            
            protect = input("Protect private key with password? (y/n): ").lower() == 'y'
            
            with open(pub_file, 'wb') as f:
                f.write(self.public_key)
            
            if protect:
                password = getpass.getpass("Enter password: ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("Passwords don't match!")
                    return
                
                protected = self.crypto.protect_private_key(self.private_key, password)
                with open(priv_file, 'wb') as f:
                    f.write(protected)
                print("Private key saved (password protected)")
            else:
                with open(priv_file, 'wb') as f:
                    f.write(self.private_key.to_bytes())
                print("Private key saved (unprotected)")
            
            print(f"Public key saved to: {pub_file}")
            
        except Exception as e:
            print(f"Error saving keypair: {e}")
    
    def encrypt_file(self):
        """Encrypt a file"""
        if not self.public_key:
            print("No public key available.")
            return
        
        try:
            input_file = input("Input file path: ").strip()
            if not os.path.exists(input_file):
                print(f"File not found: {input_file}")
                return
            
            output_file = input("Output file path (.x25): ").strip()
            if not output_file.endswith('.x25'):
                output_file += '.x25'
            
            print("Encrypting file...")
            fingerprint = self.crypto.encrypt_file(
                input_file, output_file, self.public_key, self.progress_display
            )
            print(f"File encrypted successfully!")
            print(f"Output: {output_file}")
            print(f"Fingerprint: {fingerprint}")
            
        except Exception as e:
            print(f"Encryption error: {e}")
    
    def decrypt_file(self):
        """Decrypt a file"""
        if not self.private_key:
            print("No private key available.")
            return
        
        try:
            input_file = input("Encrypted file path: ").strip()
            if not os.path.exists(input_file):
                print(f"File not found: {input_file}")
                return
            
            output_file = input("Output file path: ").strip()
            
            print("Decrypting file...")
            success = self.crypto.decrypt_file(
                input_file, output_file, self.private_key, self.progress_display
            )
            
            if success:
                print(f"File decrypted successfully!")
                print(f"Output: {output_file}")
            
        except Exception as e:
            print(f"Decryption error: {e}")
    
    def view_file_metadata(self):
        """View encrypted file metadata"""
        try:
            file_path = input("Encrypted file path: ").strip()
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return
            
            metadata = self.crypto.read_file_metadata(file_path)
            
            print(f"\nMetadata for {file_path}:")
            print("-" * 40)
            print(f"Version: {metadata['version']}")
            print(f"KEM Algorithm: {metadata['kem_algo']}")
            print(f"AEAD Algorithm: {metadata['aead_algo']}")
            print(f"Original Size: {metadata['original_size']} bytes")
            print(f"Fingerprint: {metadata['pub_fingerprint']}")
            print(f"Timestamp: {metadata['timestamp_utc']}")
            
        except Exception as e:
            print(f"Error reading metadata: {e}")
    
    def protect_private_key(self):
        """Protect private key with password"""
        if not self.private_key:
            print("No private key available.")
            return
        
        try:
            output_file = input("Output file for protected key: ").strip()
            password = getpass.getpass("Enter password: ")
            confirm = getpass.getpass("Confirm password: ")
            
            if password != confirm:
                print("Passwords don't match!")
                return
            
            protected = self.crypto.protect_private_key(self.private_key, password)
            with open(output_file, 'wb') as f:
                f.write(protected)
            
            print(f"Private key protected and saved to: {output_file}")
            
        except Exception as e:
            print(f"Error protecting key: {e}")
    
    def secret_sharing_menu(self):
        """Secret sharing submenu"""
        print("\nSecret Sharing Options:")
        print("1. Split private key")
        print("2. Reconstruct private key")
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == '1':
            self.split_private_key()
        elif choice == '2':
            self.reconstruct_private_key()
        else:
            print("Invalid choice.")
    
    def split_private_key(self):
        """Split private key using Shamir's Secret Sharing"""
        if not self.private_key:
            print("No private key available.")
            return
        
        try:
            threshold = int(input("Threshold (min shares needed): "))
            total_shares = int(input("Total number of shares: "))
            
            if threshold > total_shares or threshold < 2:
                print("Invalid threshold or share count!")
                return
            
            password = getpass.getpass("Password for key protection: ")
            base_name = input("Base name for share files: ").strip()
            
            shares = self.crypto.split_key_with_sss(
                self.private_key, password, threshold, total_shares
            )
            
            for i, share in enumerate(shares, 1):
                share_file = f"{base_name}_share_{i:02d}.sss"
                with open(share_file, 'wb') as f:
                    f.write(share)
                print(f"Share {i} saved to: {share_file}")
            
            print(f"Key split into {total_shares} shares (threshold: {threshold})")
            
        except Exception as e:
            print(f"Error splitting key: {e}")
    
    def reconstruct_private_key(self):
        """Reconstruct private key from shares"""
        try:
            num_shares = int(input("Number of share files: "))
            
            shares = []
            for i in range(num_shares):
                share_file = input(f"Share file {i+1} path: ").strip()
                if not os.path.exists(share_file):
                    print(f"Share file not found: {share_file}")
                    return
                
                with open(share_file, 'rb') as f:
                    shares.append(f.read())
            
            password = getpass.getpass("Enter password: ")
            reconstructed_key = self.crypto.reconstruct_key_from_sss(shares, password)
            
            use_key = input("Use as current private key? (y/n): ").lower() == 'y'
            if use_key:
                self.private_key = reconstructed_key
                print("Private key reconstructed and loaded!")
            else:
                output_file = input("Save to file path: ").strip()
                with open(output_file, 'wb') as f:
                    f.write(reconstructed_key.to_bytes())
                print(f"Reconstructed key saved to: {output_file}")
            
        except Exception as e:
            print(f"Error reconstructing key: {e}")
    
    def show_current_key_info(self):
        """Display current key information"""
        print("\nCurrent Key Information:")
        print("-" * 40)
        
        if self.public_key:
            print(f"Public Key: Available ({len(self.public_key)} bytes)")
            print(f"Fingerprint: {self.fingerprint}")
        else:
            print("Public Key: Not available")
        
        if self.private_key:
            print(f"Private Key: Available ({len(self.private_key)} bytes)")
        else:
            print("Private Key: Not available")
        
        print(f"Algorithm: {self.crypto.kem_algo}")
        print(f"Encryption: AES-256-GCM")
        print(f"Key Derivation: HKDF-SHA256")
    
    def run(self):
        """Main menu loop"""
        self.display_banner()
        
        while True:
            try:
                self.display_menu()
                choice = self.get_menu_choice()
                
                if choice == 0:
                    print("Goodbye!")
                    break
                elif choice == 1:
                    self.generate_keypair()
                elif choice == 2:
                    self.load_keypair()
                elif choice == 3:
                    self.save_keypair()
                elif choice == 4:
                    self.encrypt_file()
                elif choice == 5:
                    self.decrypt_file()
                elif choice == 6:
                    self.view_file_metadata()
                elif choice == 7:
                    self.protect_private_key()
                elif choice == 8:
                    self.secret_sharing_menu()
                elif choice == 9:
                    self.show_current_key_info()
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                input("\nPress Enter to continue...")


def demo_x25519_encryption():
    """Demonstration of X25519 encryption features"""
    print("=== X25519 File Encryption Demo ===\n")
    
    crypto = X25519FileEncryption()
    
    # Generate keypair
    public_key, private_key, fingerprint = crypto.generate_keypair()
    print(f"Generated keypair - Fingerprint: {fingerprint}")
    
    # Create test file
    test_data = b"This is a test file for X25519 encryption demo!" * 50
    with open("demo_test.txt", "wb") as f:
        f.write(test_data)
    
    print(f"\nCreated test file ({len(test_data)} bytes)")
    
    # Encrypt file
    print("Encrypting file...")
    crypto.encrypt_file("demo_test.txt", "demo_encrypted.x25", public_key)
    print("File encrypted successfully!")
    
    # View metadata
    metadata = crypto.read_file_metadata("demo_encrypted.x25")
    print(f"\nEncrypted file metadata:")
    print(f"- Algorithm: {metadata['kem_algo']}")
    print(f"- Size: {metadata['original_size']} bytes")
    print(f"- Fingerprint: {metadata['pub_fingerprint']}")
    
    # Decrypt file
    print("\nDecrypting file...")
    with private_key:
        crypto.decrypt_file("demo_encrypted.x25", "demo_decrypted.txt", private_key)
    print("File decrypted successfully!")
    
    # Verify integrity
    with open("demo_decrypted.txt", "rb") as f:
        decrypted_data = f.read()
    
    if decrypted_data == test_data:
        print("Integrity check: PASSED")
    else:
        print("Integrity check: FAILED")
    
    # Test key protection
    print("\nTesting key protection...")
    protected_key = crypto.protect_private_key(private_key, "demo_password")
    print(f"Key protected ({len(protected_key)} bytes)")
    
    unprotected_key = crypto.unprotect_private_key(protected_key, "demo_password")
    with unprotected_key:
        if unprotected_key.to_bytes() == private_key.to_bytes():
            print("Key protection test: PASSED")
        else:
            print("Key protection test: FAILED")
    
    # Cleanup
    cleanup_files = ["demo_test.txt", "demo_encrypted.x25", "demo_decrypted.txt"]
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            os.unlink(file_path)
    
    print("\n=== Demo completed successfully! ===")


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--demo":
            demo_x25519_encryption()
        else:
            menu = X25519CryptoMenu()
            menu.run()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted.")
    except Exception as e:
        print(f"\nProgram error: {e}")
        import traceback
        traceback.print_exc()