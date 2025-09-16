# Direct Process Communication Implementation

This document describes the changes made to replace the FastAPI server with direct process communication between the Flutter frontend and Python backend.

## Changes Made

### 1. Backend Changes

#### New CLI Script (`backend/stegocrypt_cli.py`)
- Created a command-line interface that can be called directly from Flutter
- Supports all steganography operations: image, audio, video, and text
- Supports encryption/decryption with AES and RSA
- Returns JSON responses for easy parsing by Flutter
- Handles all the same operations as the previous FastAPI server

#### Test Script (`backend/test_cli.py`)
- Simple test script to verify the CLI functionality
- Tests algorithms, encryption, and decryption operations

### 2. Frontend Changes

#### Updated API Service (`frontend/lib/services/api_service.dart`)
- Replaced HTTP requests with direct process calls using `Process.run()`
- Removed dependency on `dio` package for HTTP requests
- Added `path` package for file path handling
- All methods now call the Python CLI script directly
- Maintains the same API interface for existing pages

#### Updated Steganography Pages
- **Image Stego Page**: Updated to use new API methods
- **Audio Stego Page**: Updated to use new API methods  
- **Video Stego Page**: Updated to use new API methods
- **Text Stego Page**: Updated to use new API methods
- All pages now check backend connectivity using the CLI script
- Added proper error handling and user feedback

### 3. Dependencies

#### Added to `pubspec.yaml`
- `path: ^1.8.3` - For file path operations

#### Removed Dependencies
- No longer requires `dio` package for HTTP requests
- No longer requires running a local server

## How It Works

1. **Flutter Frontend**: When a user performs an operation (encode/decode), the Flutter app calls the appropriate method in `ApiService`
2. **Process Execution**: The `ApiService` uses `Process.run()` to execute the Python CLI script with the required parameters
3. **Python Backend**: The CLI script processes the request using the existing steganography modules
4. **Response**: The CLI returns a JSON response that Flutter parses and displays to the user

## Benefits

1. **No Server Required**: Eliminates the need to run a separate FastAPI server
2. **Direct Communication**: More efficient communication without HTTP overhead
3. **Simplified Deployment**: No need to manage server processes
4. **Better Error Handling**: Direct process communication provides clearer error messages
5. **Cross-Platform**: Works on all platforms where Python is available

## Requirements

- Python 3.x with required packages (see `backend/requirements.txt`)
- Flutter with the updated dependencies
- The Python CLI script must be executable from the Flutter app's working directory

## Usage

The Flutter app will automatically detect if the Python backend is available and show appropriate status messages. Users can perform all steganography operations as before, but now without needing to start a separate server.

## Testing

Run the test script to verify the CLI works:
```bash
cd backend
python test_cli.py
```

The Flutter app will also test connectivity automatically when launched.
