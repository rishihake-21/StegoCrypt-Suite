import os, sys

# Ensure Backend is on sys.path for local script execution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from validation.inputs import non_empty_string
from validation.media import ensure_text_capacity


def encode_txt_data(text,input_file,resultfile):
    non_empty_string(text, "text")
    l=len(text)
    i=0
    add=''
    while i<l:
        t=ord(text[i])
        if(t>=32 and t<=64):
            t1=t+48    
            res = bin(t1)[2:].zfill(8)
            add+="0011"+res
        
        else:
            t1=t-48
            res = bin(t1)[2:].zfill(8)
            add+="0110"+res
        i+=1
    res1=add+"111111111111"
    print("The string after binary conversion appyling all the transformation :- " + (res1))   
    length = len(res1)
    print("Length of binary after conversion:- ",length)
    HM_SK=""
    ZWC={"00":u'\u200C',"01":u'\u202C',"11":u'\u202D',"10":u'\u200E'}      
    file1 = open(input_file,"r+")
    file3= open(resultfile,"w+", encoding="utf-8")
    word=[]
    for line in file1: 
        word+=line.split()
    i=0
    # Centralized capacity check: each word can carry 12 bits
    try:
        ensure_text_capacity(length, len(word))
    except Exception:
        file1.close()
        file3.close()
        raise

    while(i<len(res1)):  
        s=word[int(i/12)]
        j=0
        x=""
        HM_SK=""
        while(j<12):
            x=res1[j+i]+res1[i+j+1]
            HM_SK+=ZWC[x]
            j+=2
        s1=s+HM_SK
        file3.write(s1)
        file3.write(" ")
        i+=12
    t=int(len(res1)/12)     
    while t<len(word): 
        file3.write(word[t])
        file3.write(" ")
        t+=1
    file3.close()  
    file1.close()
    print("\nStego file has successfully generated")


def check_size(text1,inputfile):
    count2=0
    file1 = open(inputfile,"r")
    for line in file1: 
        for word in line.split():
            count2=count2+1
    file1.close()       
    bt=int(count2)
    print("Maximum number of words that can be inserted :- ",int(bt/6))
    l=len(text1)
    if(l<=bt):
        print("\nInputed message can be hidden in the cover file\n")
        return True
    else:
        print("\nString is too big please reduce string size")
        return False
    
def BinaryToDecimal(binary):
    string = int(binary, 2)
    return string


def decode_txt_data(stego):
    ZWC_reverse={u'\u200C':"00",u'\u202C':"01",u'\u202D':"11",u'\u200E':"10"}
    file4= open(stego,"r", encoding="utf-8")
    temp=''
    for line in file4: 
        for words in line.split():
            T1=words
            binary_extract=""
            for letter in T1:
                if(letter in ZWC_reverse):
                    binary_extract+=ZWC_reverse[letter]
            if binary_extract=="111111111111":
                break
            else:
                temp+=binary_extract
    print("\nEncrypted message presented in code bits:",temp) 
    lengthd = len(temp)
    print("\nLength of encoded bits:- ",lengthd)
    i=0
    a=0
    b=4
    c=4
    d=12
    final=''
    while i<len(temp):
        t3=temp[a:b]
        a+=12
        b+=12
        i+=12
        t4=temp[c:d]
        c+=12
        d+=12
        if(t3=='0110'):
            decimal_data = BinaryToDecimal(t4)
            final+=chr(decimal_data  + 48)
        elif(t3=='0011'):
            decimal_data = BinaryToDecimal(t4)
            final+=chr(decimal_data  - 48)
    print("\nMessage after decoding from the stego file:- ",final)

def main():
    while True:
        print("\nTEXT STEGANOGRAPHY MENU") 
        print("1. Encode the Text message")  
        print("2. Decode the Text message")  
        print("3. Exit")  
        choice1 = int(input("Enter the Choice:"))   
        if choice1 == 1:
            text1=input("\nEnter data to be encoded:- ")
            input_file = input("\nEnter the name of the input file(with extension):- ")
            result_file = input("\nEnter the name of the Stego file after Encoding(with extension):- ")
            if check_size(text1,input_file):
                encode_txt_data(text1,input_file,result_file)                
        elif choice1 == 2:
            stego=input("\nPlease enter the stego file name(with extension) to decode the message:- ")
            decode_txt_data(stego) 
        elif choice1 == 3:
            break
        else:
            print("Incorrect Choice")
        print("\n")

if __name__ == "__main__":
    main()