# To convert text to binary
def text_to_bin(text):
    return ''.join(format(ord(c), '08b') for c in text)

def add_demiliter(msg):
    return msg + "*^*^*"