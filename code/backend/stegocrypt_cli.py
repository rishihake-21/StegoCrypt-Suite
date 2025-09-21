#!/usr/bin/env python3
"""
StegoCrypt Suite - Command Line Interface
Direct process communication interface for Flutter frontend
"""

import os
import sys
import json

# Set stdout and stderr to utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')
import argparse
import tempfile
import base64
from pathlib import Path
from typing import Optional

# Add backend directory to path for imports
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import existing modules
from steganography.image_stego import encode_image, decode_image
from steganography.audio_stego import encode_audio, decode_audio
from steganography.video_stego import (
    encode_video,
    decode_video,
)
from steganography.text_stego import (
    encode_text_data,
    decode_text_data,
)
from hashing import hash_message, verify_hash, get_supported_algorithms
from logs import log_operation, get_logs, get_log_stats
from cryptography.aes_crypto import encrypt_aes, decrypt_aes, get_key_from_password
from Crypto.Protocol.KDF import PBKDF2
from cryptography.rsa_crypto import (
    generate_rsa_keys,
    encrypt_with_rsa,
    decrypt_with_rsa,
    import_keys,
    export_keys,
    load_keys,
)
from validation.inputs import non_empty_string
from validation.errors import ValidationError

def encrypt_message(message: str, method: str, password: Optional[str] = None) -> str:
    """Encrypt message using specified method"""
    try:
        non_empty_string(message, "message")
        non_empty_string(method, "method")

        if method.upper() == "AES":
            if not password:
                raise ValueError("Password is required for AES encryption")
            key, salt = get_key_from_password(password)
            encrypted_data = encrypt_aes(key, message)
            payload = salt + encrypted_data
            # return encrypted_data
            return base64.b64encode(payload).decode('utf-8')

        elif method.upper() == "RSA":
            _, public_key = load_keys()
            if not public_key:
                generate_rsa_keys()
                _, public_key = load_keys()
            
            encrypted_data = encrypt_with_rsa(public_key, message)
            return base64.b64encode(encrypted_data).decode('utf-8')

        else:
            raise ValueError(f"Unsupported encryption method: {method}")

    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")


def decrypt_message(ciphertext: str, method: str, password: Optional[str] = None) -> str:
    """Decrypt message using specified method"""
    try:
        non_empty_string(ciphertext, "ciphertext")
        non_empty_string(method, "method")
        
        encrypted_data = base64.b64decode(ciphertext)

        if method.upper() == "AES":
            if not password:
                raise ValueError("Password is required for AES decryption")
            try:
                if len(encrypted_data) >= 48:
                    salt = encrypted_data[:16]
                    body = encrypted_data[16:]
                    key = PBKDF2(password.encode(), salt, dkLen=16, count=100000)
                    return decrypt_aes(key, body)
                else:
                    key, _ = get_key_from_password(password)
                    return decrypt_aes(key, encrypted_data)
            except Exception:
                key, _ = get_key_from_password(password)
                return decrypt_aes(key, encrypted_data)

        elif method.upper() == "RSA":
            private_key, _ = load_keys()
            if not private_key:
                raise ValueError("RSA private key not found. Cannot decrypt.")
            return decrypt_with_rsa(private_key, encrypted_data)

        else:
            raise ValueError(f"Unsupported decryption method: {method}")

    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")

def process_image_encode(args):
    """Process image encoding request"""
    try:
        log_operation("ENCODE_IMAGE", "STARTED", {"filename": os.path.basename(args.input_file)})
        
        # Encrypt the message first
        password = args.password if hasattr(args, 'password') else None
        encrypted_message = encrypt_message(args.message, args.algorithm, password)
        
        # Encode the encrypted message into the image and get the bytes
        encoded_image_bytes = encode_image(args.input_file, encrypted_message)
        
        # Base64 encode the bytes to send as a string in JSON
        encoded_image_base64 = base64.b64encode(encoded_image_bytes).decode('utf-8')
        
        output_filename = args.output_file
        if not output_filename.lower().endswith('.png'):
            output_filename += '.png'

        log_operation("ENCODE_IMAGE", "SUCCESS", {"filename": os.path.basename(output_filename)})
        return {
            "status": "success",
            "success": True,
            "message": "Message successfully encoded into image",
            "image_data": encoded_image_base64,
            "filename": os.path.basename(output_filename),
        }
        
    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("ENCODE_IMAGE", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_image_decode(args):
    """Process image decoding request"""
    try:
        log_operation("DECODE_IMAGE", "STARTED", {"filename": os.path.basename(args.input_file)})
        
        # Decode the message from the image
        decoded_text = decode_image(args.input_file)
        
        if decoded_text is None:
            log_operation(
                "DECODE_IMAGE",
                "FAILED",
                {
                    "reason": "No hidden message found",
                    "filename": os.path.basename(args.input_file),
                },
            )
            return {"status": "error", "success": False, "message": "No hidden message found in image"}
        
        # Decrypt the message
        password = args.password if hasattr(args, 'password') else None
        decrypted_message = decrypt_message(decoded_text, args.algorithm, password)
        
        log_operation("DECODE_IMAGE", "SUCCESS", {"filename": os.path.basename(args.input_file)})
        return {
            "status": "success",
            "success": True,
            "message": decrypted_message,
            "ciphertext": decoded_text,
        }
        
    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("DECODE_IMAGE", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_audio_encode(args):
    """Process audio encoding request"""
    try:
        log_operation("ENCODE_AUDIO", "STARTED", {"filename": os.path.basename(args.input_file)})
        
        password = args.password if hasattr(args, 'password') else None
        encrypted_message = encrypt_message(args.message, args.algorithm, password)
        
        encoded_audio_bytes = encode_audio(args.input_file, encrypted_message)
        
        encoded_audio_base64 = base64.b64encode(encoded_audio_bytes).decode('utf-8')
        
        log_operation("ENCODE_AUDIO", "SUCCESS", {"filename": os.path.basename(args.output_file)})
        return {
            "status": "success",
            "success": True,
            "message": "Message successfully encoded into audio",
            "audio_data": encoded_audio_base64,
            "filename": os.path.basename(args.output_file),
        }
        
    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("ENCODE_AUDIO", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_audio_decode(args):
    """Process audio decoding request"""
    try:
        log_operation("DECODE_AUDIO", "STARTED", {"filename": os.path.basename(args.input_file)})
        
        decoded_text = decode_audio(args.input_file)
        
        if decoded_text is None:
            log_operation(
                "DECODE_AUDIO",
                "FAILED",
                {
                    "reason": "No hidden message found",
                    "filename": os.path.basename(args.input_file),
                },
            )
            return {"status": "error", "success": False, "message": "No hidden message found in audio"}
        
        password = args.password if hasattr(args, 'password') else None
        decrypted_message = decrypt_message(decoded_text, args.algorithm, password)
        
        log_operation("DECODE_AUDIO", "SUCCESS", {"filename": os.path.basename(args.input_file)})
        return {
            "status": "success",
            "success": True,
            "message": decrypted_message,
            "ciphertext": decoded_text,
        }
        
    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("DECODE_AUDIO", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_video_encode(args):
    """Process video encoding request"""
    try:
        log_operation("ENCODE_VIDEO", "STARTED", {"filename": os.path.basename(args.input_file)})
        
        # Encrypt the message first
        password = args.password if hasattr(args, 'password') else None
        encrypted_message = encrypt_message(args.message, args.algorithm, password)
        
        # Encode the encrypted message into the video and get the bytes
        encoded_video_bytes = encode_video(args.input_file, encrypted_message)
        
        # Base64 encode the bytes to send as a string in JSON
        encoded_video_base64 = base64.b64encode(encoded_video_bytes).decode('utf-8')
        
        log_operation("ENCODE_VIDEO", "SUCCESS", {"filename": os.path.basename(args.output_file)})
        return {
            "status": "success",
            "success": True,
            "message": "Message successfully encoded into video",
            "video_data": encoded_video_base64,
            "filename": os.path.basename(args.output_file),
        }
        
    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("ENCODE_VIDEO", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_video_decode(args):
    """Process video decoding request"""
    try:
        log_operation("DECODE_VIDEO", "STARTED", {"filename": os.path.basename(args.input_file)})
        
        # Decode the message from the video
        with open(args.input_file, "rb") as f:
            video_bytes = f.read()

        decoded_text = decode_video(video_bytes)
        
        if decoded_text is None:
            log_operation(
                "DECODE_VIDEO",
                "FAILED",
                {
                    "reason": "No hidden message found",
                    "filename": os.path.basename(args.input_file),
                },
            )
            return {"status": "error", "success": False, "message": "No hidden message found in video"}
        
        # Decrypt the message
        password = args.password if hasattr(args, 'password') else None
        decrypted_message = decrypt_message(decoded_text, args.algorithm, password)
        
        log_operation("DECODE_VIDEO", "SUCCESS", {"filename": os.path.basename(args.input_file)})
        return {
            "status": "success",
            "success": True,
            "message": decrypted_message,
            "ciphertext": decoded_text,
        }
        
    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("DECODE_VIDEO", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_text_encode(args):
    """Process text encoding request"""
    try:
        log_operation("ENCODE_TEXT", "STARTED", {"filename": os.path.basename(args.input_file)})

        password = args.password if hasattr(args, 'password') else None
        encrypted_message = encrypt_message(args.message, args.algorithm, password)

        with open(args.input_file, 'r', encoding='utf-8') as f:
            cover_text = f.read()

        encoded_text = encode_text_data(encrypted_message, cover_text)
        
        encoded_text_base64 = base64.b64encode(encoded_text.encode('utf-8')).decode('utf-8')

        log_operation("ENCODE_TEXT", "SUCCESS", {"filename": os.path.basename(args.output_file)})
        return {
            "status": "success",
            "success": True,
            "message": "Message successfully encoded into text",
            "text_data": encoded_text_base64,
            "filename": os.path.basename(args.output_file),
        }

    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("ENCODE_TEXT", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_text_decode(args):
    """Process text decoding request"""
    try:
        log_operation("DECODE_TEXT", "STARTED", {"filename": os.path.basename(args.input_file)})

        with open(args.input_file, 'r', encoding='utf-8') as f:
            stego_text = f.read()

        decoded_text = decode_text_data(stego_text)
        if not decoded_text:
            log_operation(
                "DECODE_TEXT",
                "FAILED",
                {
                    "reason": "No hidden message found",
                    "filename": os.path.basename(args.input_file),
                },
            )
            return {"status": "error", "success": False, "message": "No hidden message found in text"}

        password = args.password if hasattr(args, 'password') else None
        decrypted_message = decrypt_message(decoded_text, args.algorithm, password)

        log_operation("DECODE_TEXT", "SUCCESS", {"filename": os.path.basename(args.input_file)})
        return {
            "status": "success",
            "success": True,
            "message": decrypted_message,
            "ciphertext": decoded_text,
        }

    except Exception as e:
        details = {"error": str(e)}
        if hasattr(args, 'input_file') and args.input_file:
            details["filename"] = os.path.basename(args.input_file)
        log_operation("DECODE_TEXT", "FAILED", details)
        return {"status": "error", "success": False, "message": str(e)}

def process_encrypt(args):
    """Process encryption request"""
    try:
        log_operation("ENCRYPT", "STARTED", {"method": args.method})
        password = args.password if hasattr(args, 'password') else None
        ciphertext = encrypt_message(args.message, args.method, password)
        log_operation("ENCRYPT", "SUCCESS", {"method": args.method})
        return {"status": "success", "ciphertext": ciphertext}
    except Exception as e:
        log_operation("ENCRYPT", "FAILED", {"error": str(e)})
        return {"status": "error", "message": str(e)}

def process_decrypt(args):
    """Process decryption request"""
    try:
        log_operation("DECRYPT", "STARTED", {"method": args.method})
        password = args.password if hasattr(args, 'password') else None
        message = decrypt_message(args.ciphertext, args.method, password)
        log_operation("DECRYPT", "SUCCESS", {"method": args.method})
        return {"status": "success", "message": message}
    except Exception as e:
        log_operation("DECRYPT", "FAILED", {"error": str(e)})
        return {"status": "error", "message": str(e)}

def process_hash(args):
    """Process hashing request"""
    try:
        log_operation("HASH", "STARTED", {"algorithm": args.algorithm})
        hash_value = hash_message(args.message, args.algorithm)
        log_operation("HASH", "SUCCESS", {"algorithm": args.algorithm})
        return {"status": "success", "hash": hash_value, "algorithm": args.algorithm}
    except Exception as e:
        log_operation("HASH", "FAILED", {"error": str(e)})
        return {"status": "error", "message": str(e)}

def process_verify_hash(args):
    """Process hash verification request"""
    try:
        log_operation("VERIFY_HASH", "STARTED", {"algorithm": args.algorithm})
        is_valid = verify_hash(args.message, args.hash_value, args.algorithm)
        log_operation("VERIFY_HASH", "SUCCESS" if is_valid else "FAILED", {"algorithm": args.algorithm})
        return {"status": "success", "valid": is_valid, "algorithm": args.algorithm}
    except Exception as e:
        log_operation("VERIFY_HASH", "FAILED", {"error": str(e)})
        return {"status": "error", "message": str(e)}

def process_algorithms(args):
    """Get supported algorithms"""
    return {
        "status": "success",
        "encryption": ["AES", "RSA"],
        "hashing": get_supported_algorithms()
    }

def process_get_logs(args):
    """Process get logs request"""
    try:
        logs = get_logs()
        return {"status": "success", "logs": logs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_get_log_stats(args):
    """Process get log stats request"""
    try:
        stats = get_log_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_rsa_command(args):
    """Process RSA-related commands"""
    try:
        if args.rsa_command == "generate-keys":
            output_dir = args.output_dir if hasattr(args, 'output_dir') else None
            private_key_path, public_key_path = generate_rsa_keys(output_dir)
            return {
                "status": "success",
                "message": f"RSA keys generated and saved to {private_key_path.parent}",
            }
        elif args.rsa_command == "import-keys":
            import_keys(args.pub_file, args.priv_file)
            return {"status": "success", "message": "RSA keys imported successfully"}
        elif args.rsa_command == "export-keys":
            export_keys(args.output_dir)
            return {
                "status": "success",
                "message": f"RSA keys exported to {args.output_dir}",
            }
        elif args.rsa_command == "encrypt":
            _, public_key = load_keys()
            encrypted = encrypt_with_rsa(public_key, args.message)
            return {"status": "success", "ciphertext": base64.b64encode(encrypted).decode('utf-8')}
        elif args.rsa_command == "decrypt":
            private_key, _ = load_keys()
            decrypted = decrypt_with_rsa(private_key, base64.b64decode(args.ciphertext))
            return {"status": "success", "message": decrypted}
        else:
            return {"status": "error", "message": f"Unknown RSA command: {args.rsa_command}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    parser = argparse.ArgumentParser(description='StegoCrypt Suite CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Image steganography
    img_encode_parser = subparsers.add_parser('encode-image')
    img_encode_parser.add_argument('--message', required=True)
    img_encode_parser.add_argument('--password', required=False)
    img_encode_parser.add_argument('--algorithm', required=True)
    img_encode_parser.add_argument('--input-file', required=True)
    img_encode_parser.add_argument('--output-file', required=True)
    
    img_decode_parser = subparsers.add_parser('decode-image')
    img_decode_parser.add_argument('--password', required=False)
    img_decode_parser.add_argument('--algorithm', required=True)
    img_decode_parser.add_argument('--input-file', required=True)
    
    # Audio steganography
    aud_encode_parser = subparsers.add_parser('encode-audio')
    aud_encode_parser.add_argument('--message', required=True)
    aud_encode_parser.add_argument('--password', required=False)
    aud_encode_parser.add_argument('--algorithm', required=True)
    aud_encode_parser.add_argument('--input-file', required=True)
    aud_encode_parser.add_argument('--output-file', required=True)
    
    aud_decode_parser = subparsers.add_parser('decode-audio')
    aud_decode_parser.add_argument('--password', required=False)
    aud_decode_parser.add_argument('--algorithm', required=True)
    aud_decode_parser.add_argument('--input-file', required=True)
    
    # Video steganography
    vid_encode_parser = subparsers.add_parser('encode-video')
    vid_encode_parser.add_argument('--message', required=True)
    vid_encode_parser.add_argument('--password', required=False)
    vid_encode_parser.add_argument('--algorithm', required=True)
    vid_encode_parser.add_argument('--input-file', required=True)
    vid_encode_parser.add_argument('--output-file', required=True)
    
    vid_decode_parser = subparsers.add_parser('decode-video')
    vid_decode_parser.add_argument('--password', required=False)
    vid_decode_parser.add_argument('--algorithm', required=True)
    vid_decode_parser.add_argument('--input-file', required=True)
    
    # Text steganography
    txt_encode_parser = subparsers.add_parser('encode-text')
    txt_encode_parser.add_argument('--message', required=True)
    txt_encode_parser.add_argument('--password', required=False)
    txt_encode_parser.add_argument('--algorithm', required=True)
    txt_encode_parser.add_argument('--input-file', required=True)
    txt_encode_parser.add_argument('--output-file', required=True)
    
    txt_decode_parser = subparsers.add_parser('decode-text')
    txt_decode_parser.add_argument('--password', required=False)
    txt_decode_parser.add_argument('--algorithm', required=True)
    txt_decode_parser.add_argument('--input-file', required=True)
    
    # Encryption/Decryption
    encrypt_parser = subparsers.add_parser('encrypt')
    encrypt_parser.add_argument('--message', required=True)
    encrypt_parser.add_argument('--password', required=False)
    encrypt_parser.add_argument('--method', required=True)
    
    decrypt_parser = subparsers.add_parser('decrypt')
    decrypt_parser.add_argument('--ciphertext', required=True)
    decrypt_parser.add_argument('--password', required=False)
    decrypt_parser.add_argument('--method', required=True)
    
    # Hashing
    hash_parser = subparsers.add_parser('hash')
    hash_parser.add_argument('--message', required=True)
    hash_parser.add_argument('--algorithm', default='sha256')
    
    verify_hash_parser = subparsers.add_parser('verify-hash')
    verify_hash_parser.add_argument('--message', required=True)
    verify_hash_parser.add_argument('--hash-value', required=True)
    verify_hash_parser.add_argument('--algorithm', default='sha256')
    
    # Algorithms
    algorithms_parser = subparsers.add_parser('algorithms')

    # Logs
    logs_parser = subparsers.add_parser('get-logs')
    log_stats_parser = subparsers.add_parser('get-log-stats')

    # RSA commands
    rsa_parser = subparsers.add_parser('rsa', help='RSA key management')
    rsa_subparsers = rsa_parser.add_subparsers(dest='rsa_command', help='RSA commands')

    rsa_generate_parser = rsa_subparsers.add_parser('generate-keys', help='Generate RSA key pair')
    rsa_generate_parser.add_argument('--output-dir', required=False, help='Directory to save the generated keys')
    
    rsa_import_parser = rsa_subparsers.add_parser('import-keys', help='Import RSA key pair')
    rsa_import_parser.add_argument('--pub-file', required=True, help='Path to public key file')
    rsa_import_parser.add_argument('--priv-file', required=True, help='Path to private key file')

    rsa_export_parser = rsa_subparsers.add_parser('export-keys', help='Export RSA key pair')
    rsa_export_parser.add_argument('--output-dir', required=True, help='Directory to save keys')

    rsa_encrypt_parser = rsa_subparsers.add_parser('encrypt', help='Encrypt a message with RSA')
    rsa_encrypt_parser.add_argument('--message', required=True, help='Message to encrypt')

    rsa_decrypt_parser = rsa_subparsers.add_parser('decrypt', help='Decrypt a message with RSA')
    rsa_decrypt_parser.add_argument('--ciphertext', required=True, help='Ciphertext to decrypt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Route to appropriate handler
        if args.command == 'encode-image':
            result = process_image_encode(args)
        elif args.command == 'decode-image':
            result = process_image_decode(args)
        elif args.command == 'encode-audio':
            result = process_audio_encode(args)
        elif args.command == 'decode-audio':
            result = process_audio_decode(args)
        elif args.command == 'encode-video':
            result = process_video_encode(args)
        elif args.command == 'decode-video':
            result = process_video_decode(args)
        elif args.command == 'encode-text':
            result = process_text_encode(args)
        elif args.command == 'decode-text':
            result = process_text_decode(args)
        elif args.command == 'encrypt':
            result = process_encrypt(args)
        elif args.command == 'decrypt':
            result = process_decrypt(args)
        elif args.command == 'hash':
            result = process_hash(args)
        elif args.command == 'verify-hash':
            result = process_verify_hash(args)
        elif args.command == 'algorithms':
            result = process_algorithms(args)
        elif args.command == 'get-logs':
            result = process_get_logs(args)
        elif args.command == 'get-log-stats':
            result = process_get_log_stats(args)
        elif args.command == 'rsa':
            result = process_rsa_command(args)
        else:
            result = {"status": "error", "message": f"Unknown command: {args.command}"}
        
        # Output result as JSON
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {"status": "error", "message": str(e)}
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
