from io import BytesIO
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
        return wav_file
    return input_file

def encode_audio(input_file, message):
    wav_file = convert_to_wav(input_file)
    
    try:
        with wave.open(wav_file, mode='rb') as song:
            frame_bytes = bytearray(list(song.readframes(song.getnframes())))
            message += '###'
            bits = ''.join([format(ord(i), '08b') for i in message])

            if len(bits) > len(frame_bytes):
                raise ValueError("Message too long to encode in this audio.")

            for i, bit in enumerate(bits):
                frame_bytes[i] = (frame_bytes[i] & 254) | int(bit)

            modified_frames = bytes(frame_bytes)

            with BytesIO() as buffer:
                with wave.open(buffer, 'wb') as fd:
                    fd.setparams(song.getparams())
                    fd.writeframes(modified_frames)
                return buffer.getvalue()
    finally:
        if wav_file != input_file:
            os.remove(wav_file)

def decode_audio(encoded_file):
    try:
        with wave.open(encoded_file, mode='rb') as song:
            frame_bytes = bytearray(list(song.readframes(song.getnframes())))
            extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
            bits = ''.join([str(bit) for bit in extracted])
            chars = [bits[i:i+8] for i in range(0, len(bits), 8)]

            decoded = ""
            for byte in chars:
                if len(byte) < 8:
                    continue
                try:
                    char = chr(int(byte, 2))
                    decoded += char
                    if decoded.endswith('###'):
                        return decoded[:-3]
                except ValueError:
                    continue 
    except (FileNotFoundError, wave.Error):
        return None
    return None
