"""
Hashing utilities for StegoCrypt Suite
"""

import hashlib
import os
import sys

# Ensure Backend is on sys.path for local script execution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from validation.inputs import non_empty_string

def hash_message(message: str, algorithm: str = "sha256") -> str:
    """
    Hash a message using specified algorithm
    
    Args:
        message: The message to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
    
    Returns:
        Hex digest of the hashed message
    """
    non_empty_string(message, "message")
    non_empty_string(algorithm, "algorithm")
    
    algorithm = algorithm.lower()
    
    if algorithm == "md5":
        return hashlib.md5(message.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(message.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(message.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(message.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

def verify_hash(message: str, hash_value: str, algorithm: str = "sha256") -> bool:
    """
    Verify a message against its hash
    
    Args:
        message: The original message
        hash_value: The hash to verify against
        algorithm: Hash algorithm used
    
    Returns:
        True if hash matches, False otherwise
    """
    computed_hash = hash_message(message, algorithm)
    return computed_hash == hash_value

def get_supported_algorithms() -> list:
    """Get list of supported hash algorithms"""
    return ["md5", "sha1", "sha256", "sha512"]

def main():
    """CLI interface for hashing"""
    print("HASHING UTILITIES")
    print("1. Hash message")
    print("2. Verify hash")
    print("3. List algorithms")
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == '1':
        message = input("Enter message to hash: ").strip()
        algorithm = input("Enter algorithm (md5/sha1/sha256/sha512): ").strip() or "sha256"
        
        try:
            hash_result = hash_message(message, algorithm)
            print(f"Hash ({algorithm}): {hash_result}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == '2':
        message = input("Enter message: ").strip()
        hash_value = input("Enter hash to verify: ").strip()
        algorithm = input("Enter algorithm (md5/sha1/sha256/sha512): ").strip() or "sha256"
        
        try:
            is_valid = verify_hash(message, hash_value, algorithm)
            print(f"Hash verification: {'PASSED' if is_valid else 'FAILED'}")
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == '3':
        algorithms = get_supported_algorithms()
        print("Supported algorithms:")
        for alg in algorithms:
            print(f"  - {alg}")
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()