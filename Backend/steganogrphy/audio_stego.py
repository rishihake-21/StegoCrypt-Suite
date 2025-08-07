import wave
import os
from pydub import AudioSegment
from pydub.utils import which

AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

def convert_to_wav(input_file):
    file_name, ext = os.path.splitext(input_file)
    if ext.lower() != '.wav':
        audio = AudioSegment.from_file(input_file)
        wav_file = file_name + "_converted.wav"
        audio.export(wav_file, format="wav")
        print(f"[i] Converted to WAV: {wav_file}")
        return wav_file
    return input_file

def encode_audio(input_file, message,output_filename):
    
    wav_file = convert_to_wav(input_file)
    song = wave.open(wav_file, mode='rb')

    frame_bytes = bytearray(list(song.readframes(song.getnframes())))
    message += '###'  
    bits = ''.join([format(ord(i), '08b') for i in message])

    if len(bits) > len(frame_bytes):
        print("[!] Message too long to encode in this audio.")
        return

    for i, bit in enumerate(bits):
        frame_bytes[i] = (frame_bytes[i] & 254) | int(bit)

    modified_frames = bytes(frame_bytes)

    output_file = f"{output_filename}.wav"
    with wave.open(output_file, 'wb') as fd:
        fd.setparams(song.getparams())
        fd.writeframes(modified_frames)

    song.close()
    print(f" Message encoded and saved as: {output_file}")

def decode_audio(encoded_file):
    

    try:
        song = wave.open(encoded_file, mode='rb')
    except FileNotFoundError:
        print("[!] File not found.")
        return

    frame_bytes = bytearray(list(song.readframes(song.getnframes())))
    extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
    bits = ''.join([str(bit) for bit in extracted])
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]

    decoded = ""
    for byte in chars:
        char = chr(int(byte, 2))
        decoded += char
        if decoded[-3:] == '###':
            break

    song.close()
    if '###' in decoded:
        print("\n Decoded Message:")
        print(">", decoded[:-3])
    else:
        print("\n No valid message found.")

def main_menu():
    while True:
        print("\n AUDIO STEGANOGRAPHY MENU")
        print("1. Encode Message into Audio")
        print("2. Decode Message from Audio")
        print("3. Exit")

        choice = input("Select an option (1-3): ")

        if choice == '1':
            input_file = input("Enter input audio file (e.g., audio.mp3 or .wav): ").strip()
            message = input("Enter the message to hide: ")
            output_file = input("Enter the output audio file : ")
            encode_audio(input_file,message,output_file)
        elif choice == '2':
            encoded_file = input("Enter encoded WAV file name: ").strip()
            decode_audio(encoded_file)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main_menu()
