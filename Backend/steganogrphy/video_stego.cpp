#include <opencv2/opencv.hpp>
#include <iostream>
#include <bitset>

using namespace cv;
using namespace std;

const string START_MARK = "STEGO_START";
const string END_MARK = "STEGO_END";

// Convert text to binary string
string textToBinary(const string &text) {
    string bin;
    for (char c : text) {
        bin += bitset<8>(c).to_string();
    }
    return bin;
}

// Convert binary string to text
string binaryToText(const string &binary) {
    string text;
    for (size_t i = 0; i < binary.size(); i += 8) {
        bitset<8> bits(binary.substr(i, 8));
        text += char(bits.to_ulong());
    }
    return text;
}

// Embed binary data into frame LSB
void embedBinary(Mat &frame, const string &binary) {
    int totalBits = binary.size();
    int idx = 0;
    uchar *data = frame.data;
    int totalPixels = frame.rows * frame.cols * frame.channels();

    for (int i = 0; i < totalPixels && idx < totalBits; i++, idx++) {
        data[i] = (data[i] & ~1) | (binary[idx] - '0');
    }
}

// Extract binary data from frame LSB
string extractBinary(const Mat &frame, int bitCount) {
    string bits;
    const uchar *data = frame.data;
    int totalPixels = frame.rows * frame.cols * frame.channels();
    for (int i = 0; i < totalPixels && i < bitCount; i++) {
        bits += ((data[i] & 1) ? '1' : '0');
    }
    return bits;
}

void encodeVideo(const string &inputPath, const string &outputPath, const string &message, int frameToHide = 5) {
    VideoCapture cap(inputPath);
    if (!cap.isOpened()) {
        cerr << "[!] Could not open input video.\n";
        return;
    }

    int width = (int)cap.get(CAP_PROP_FRAME_WIDTH);
    int height = (int)cap.get(CAP_PROP_FRAME_HEIGHT);
    double fps = cap.get(CAP_PROP_FPS);
    int totalFrames = (int)cap.get(CAP_PROP_FRAME_COUNT);

    if (frameToHide <= 0 || frameToHide >= totalFrames) {
        cerr << "[!] Invalid frame number.\n";
        return;
    }

    VideoWriter out(outputPath, VideoWriter::fourcc('M','J','P','G'), fps, Size(width, height));
    if (!out.isOpened()) {
        cerr << "[!] Could not create output video writer.\n";
        return;
    }

    string fullMessage = START_MARK + message + END_MARK;
    string messageBits = textToBinary(fullMessage);

    string frameIndexBits = bitset<16>(frameToHide).to_string();

    int frameIdx = 0;
    Mat frame;
    while (cap.read(frame)) {
        if (frameIdx == 0) {
            embedBinary(frame, frameIndexBits);
        } else if (frameIdx == frameToHide) {
            embedBinary(frame, messageBits);
        }
        out.write(frame);
        frameIdx++;
    }

    cap.release();
    out.release();
    cout << "[i] Message embedded successfully in frame " << frameToHide << "\n";
}

void decodeVideo(const string &stegoPath) {
    VideoCapture cap(stegoPath);
    if (!cap.isOpened()) {
        cerr << "[!] Could not open stego video.\n";
        return;
    }

    Mat frame0;
    if (!cap.read(frame0)) {
        cerr << "[!] Could not read frame 0.\n";
        return;
    }

    string frameBits = extractBinary(frame0, 16);
    int frameToExtract = stoi(frameBits, nullptr, 2);

    cap.set(CAP_PROP_POS_FRAMES, frameToExtract);
    Mat targetFrame;
    if (!cap.read(targetFrame)) {
        cerr << "[!] Could not read target frame.\n";
        return;
    }

    // Extract more bits than needed (safe upper bound)
    string bits = extractBinary(targetFrame, targetFrame.rows * targetFrame.cols * targetFrame.channels());
    string decodedText = binaryToText(bits);

    size_t startPos = decodedText.find(START_MARK);
    size_t endPos = decodedText.find(END_MARK);

    if (startPos == string::npos || endPos == string::npos) {
        cout << "[!] No valid message found.\n";
        return;
    }

    string secret = decodedText.substr(startPos + START_MARK.size(), endPos - (startPos + START_MARK.size()));
    cout << "\nDecoded Message:\n> " << secret << "\n";
}

int main() {
    while (true) {
        cout << "\n VIDEO STEGANOGRAPHY MENU\n";
        cout << "1. Encode\n";
        cout << "2. Decode\n";
        cout << "3. Exit\n";
        cout << "Choose (1/2/3): ";
        int choice;
        cin >> choice;

        if (choice == 1) {
            string inputPath, outputPath, message;
            cout << "Enter input video path: ";
            cin >> inputPath;
            cout << "Enter output video path (e.g., stego.avi): ";
            cin >> outputPath;
            cout << "Enter the message to hide: ";
            cin.ignore();
            getline(cin, message);
            encodeVideo(inputPath, outputPath, message, 5);
        } else if (choice == 2) {
            string stegoPath;
            cout << "Enter stego video path: ";
            cin >> stegoPath;
            decodeVideo(stegoPath);
        } else if (choice == 3) {
            break;
        } else {
            cout << "Invalid choice.\n";
        }
    }
    return 0;
}
