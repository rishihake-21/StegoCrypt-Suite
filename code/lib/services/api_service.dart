import 'dart:io';
import 'dart:convert';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

class ApiService {
  late final String _pythonExecutable;
  late final String _cliScriptPath;

  ApiService() {
    _pythonExecutable = Platform.isWindows ? 'python' : 'python3';
    _cliScriptPath = path.join(Directory.current.path, 'backend', 'stegocrypt_cli.py');
  }

  /// Encode a message into an image
  Future<Map<String, dynamic>> encodeMessage({
    required String message,
    required String password,
    required String algorithm,
    required File imageFile,
  }) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final outputFile = File(path.join(tempDir.path, 'encoded_${path.basename(imageFile.path)}'));
      
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'encode-image',
          '--message', message,
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', imageFile.path,
          '--output-file', outputFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      if (response['status'] == 'success') {
        // Copy the output file to the expected location
        final finalOutputFile = File(path.join(tempDir.path, response['filename']));
        if (outputFile.existsSync()) {
          await outputFile.copy(finalOutputFile.path);
        }
        response['output_path'] = finalOutputFile.path;
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to encode message: $e');
    }
  }

  /// Decode a message from an image
  Future<Map<String, dynamic>> decodeMessage({
    required String password,
    required String algorithm,
    required File imageFile,
  }) async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'decode-image',
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', imageFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return response;
    } catch (e) {
      throw Exception('Failed to decode message: $e');
    }
  }

  /// Get encoded image file (now returns the file directly since it's created locally)
  Future<File> downloadEncodedImage(String filename) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final filePath = path.join(tempDir.path, filename);
      final file = File(filePath);
      
      if (!file.existsSync()) {
        throw Exception('File not found: $filename');
      }
      
      return file;
    } catch (e) {
      throw Exception('Failed to get image: $e');
    }
  }

  /// Get supported algorithms
  Future<List<String>> getAlgorithms() async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [_cliScriptPath, 'algorithms'],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return List<String>.from(response['encryption']);
    } catch (e) {
      throw Exception('Failed to get algorithms: $e');
    }
  }

  /// Clean up temporary files
  Future<void> cleanupFiles() async {
    try {
      final tempDir = await getTemporaryDirectory();
      final files = tempDir.listSync();
      for (final file in files) {
        if (file is File && file.path.contains('encoded_') || file.path.contains('decoded_')) {
          await file.delete();
        }
      }
    } catch (e) {
      // Ignore cleanup errors
    }
  }

  /// Check if backend is available (check if Python script exists and is executable)
  Future<bool> isBackendRunning() async {
    try {
      final scriptFile = File(_cliScriptPath);
      if (!scriptFile.existsSync()) {
        return false;
      }
      
      // Test if Python can execute the script
      final result = await Process.run(
        _pythonExecutable,
        [_cliScriptPath, '--help'],
      );
      
      return result.exitCode == 0;
    } catch (e) {
      return false;
    }
  }

  /// Encode a message into audio
  Future<Map<String, dynamic>> encodeAudioMessage({
    required String message,
    required String password,
    required String algorithm,
    required File audioFile,
  }) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final outputFile = File(path.join(tempDir.path, 'encoded_${path.basename(audioFile.path)}'));
      
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'encode-audio',
          '--message', message,
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', audioFile.path,
          '--output-file', outputFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      if (response['status'] == 'success') {
        response['output_path'] = outputFile.path;
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to encode audio message: $e');
    }
  }

  /// Decode a message from audio
  Future<Map<String, dynamic>> decodeAudioMessage({
    required String password,
    required String algorithm,
    required File audioFile,
  }) async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'decode-audio',
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', audioFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return response;
    } catch (e) {
      throw Exception('Failed to decode audio message: $e');
    }
  }

  /// Encode a message into video
  Future<Map<String, dynamic>> encodeVideoMessage({
    required String message,
    required String password,
    required String algorithm,
    required File videoFile,
  }) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final outputFile = File(path.join(tempDir.path, 'encoded_${path.basename(videoFile.path)}'));
      
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'encode-video',
          '--message', message,
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', videoFile.path,
          '--output-file', outputFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      if (response['status'] == 'success') {
        response['output_path'] = outputFile.path;
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to encode video message: $e');
    }
  }

  /// Decode a message from video
  Future<Map<String, dynamic>> decodeVideoMessage({
    required String password,
    required String algorithm,
    required File videoFile,
  }) async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'decode-video',
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', videoFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return response;
    } catch (e) {
      throw Exception('Failed to decode video message: $e');
    }
  }

  /// Encode a message into text
  Future<Map<String, dynamic>> encodeTextMessage({
    required String message,
    required String password,
    required String algorithm,
    required File textFile,
  }) async {
    try {
      final tempDir = await getTemporaryDirectory();
      final outputFile = File(path.join(tempDir.path, 'encoded_${path.basename(textFile.path)}'));
      
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'encode-text',
          '--message', message,
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', textFile.path,
          '--output-file', outputFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      if (response['status'] == 'success') {
        response['output_path'] = outputFile.path;
      }
      
      return response;
    } catch (e) {
      throw Exception('Failed to encode text message: $e');
    }
  }

  /// Decode a message from text
  Future<Map<String, dynamic>> decodeTextMessage({
    required String password,
    required String algorithm,
    required File textFile,
  }) async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'decode-text',
          '--password', password,
          '--algorithm', algorithm,
          '--input-file', textFile.path,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return response;
    } catch (e) {
      throw Exception('Failed to decode text message: $e');
    }
  }

  /// Encrypt a message
  Future<Map<String, dynamic>> encryptMessage({
    required String message,
    required String password,
    required String method,
  }) async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'encrypt',
          '--message', message,
          '--password', password,
          '--method', method,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return response;
    } catch (e) {
      throw Exception('Failed to encrypt message: $e');
    }
  }

  /// Decrypt a message
  Future<Map<String, dynamic>> decryptMessage({
    required String ciphertext,
    required String password,
    required String method,
  }) async {
    try {
      final result = await Process.run(
        _pythonExecutable,
        [
          _cliScriptPath,
          'decrypt',
          '--ciphertext', ciphertext,
          '--password', password,
          '--method', method,
        ],
      );

      if (result.exitCode != 0) {
        throw Exception('Process failed: ${result.stderr}');
      }

      final response = json.decode(result.stdout);
      return response;
    } catch (e) {
      throw Exception('Failed to decrypt message: $e');
    }
  }
}
