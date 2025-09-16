import os
import sys

# Ensure Backend is on sys.path for local script execution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from validation.inputs import non_empty_string
from validation.media import ensure_text_capacity

def encode_text_data(secret_message: str, cover_text: str) -> str:
    """
    Encodes a secret message into a cover text using Zero-Width Characters.
    """
    non_empty_string(secret_message, "secret_message")
    non_empty_string(cover_text, "cover_text")

    # 1. Convert secret message to binary representation
    add = ''
    for char in secret_message:
        t = ord(char)
        if 32 <= t <= 64:
            t1 = t + 48
            res = bin(t1)[2:].zfill(8)
            add += "0011" + res
        else:
            t1 = t - 48
            res = bin(t1)[2:].zfill(8)
            add += "0110" + res
    
    binary_string = add + "111111111111"  # Add terminator
    binary_len = len(binary_string)

    # 2. Prepare cover text and check capacity
    words = cover_text.split()
    ensure_text_capacity(binary_len, len(words))

    # 3. Embed binary data into words using Zero-Width Characters
    ZWC = {"00": u'\u200C', "01": u'\u202C', "11": u'\u202D', "10": u'\u200E'}
    
    encoded_words = []
    i = 0
    word_index = 0

    while i < binary_len:
        if word_index >= len(words):
            # This case should be prevented by ensure_text_capacity, but as a safeguard:
            raise ValueError("Not enough words in cover text for the message size.")

        s = words[word_index]
        hm_sk = ""
        j = 0
        while j < 12 and (i + j + 1) < binary_len:
            x = binary_string[i+j] + binary_string[i+j+1]
            hm_sk += ZWC[x]
            j += 2
        
        encoded_words.append(s + hm_sk)
        i += 12
        word_index += 1

    # 4. Append remaining words and join to form the final stego text
    if word_index < len(words):
        encoded_words.extend(words[word_index:])
        
    return " ".join(encoded_words)


def decode_text_data(stego_text: str) -> str:
    """
    Decodes a secret message from a steganographic text.
    """
    non_empty_string(stego_text, "stego_text")
    
    ZWC_reverse = {u'\u200C': "00", u'\u202C': "01", u'\u202D': "11", u'\u200E': "10"}
    
    temp = ''
    words = stego_text.split()

    for word in words:
        binary_extract = ""
        for letter in word:
            if letter in ZWC_reverse:
                binary_extract += ZWC_reverse[letter]
        
        if binary_extract == "111111111111":
            break
        else:
            temp += binary_extract

    # Convert binary string back to the original message
    final_message = ''
    i = 0
    while i < len(temp):
        # Each character was encoded in 12 bits (4 for type, 8 for data)
        if i + 12 > len(temp):
            break # Avoid processing incomplete chunks

        type_bits = temp[i : i+4]
        data_bits = temp[i+4 : i+12]
        
        if len(data_bits) < 8:
            break # Ensure we have a full byte to process

        decimal_data = int(data_bits, 2)

        if type_bits == '0110':
            final_message += chr(decimal_data + 48)
        elif type_bits == '0011':
            final_message += chr(decimal_data - 48)
            
        i += 12
        
    return final_message
