import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ChangePasswordPage extends StatefulWidget {
  const ChangePasswordPage({super.key});

  @override
  State<ChangePasswordPage> createState() => _ChangePasswordPageState();
}

class _ChangePasswordPageState extends State<ChangePasswordPage> {
  final TextEditingController _oldPasswordController = TextEditingController();
  final TextEditingController _newPasswordController = TextEditingController();
  final TextEditingController _confirmPasswordController =
      TextEditingController();
  String? _errorText;

  Future<String> _hashPassword(String password) async {
    final result = await Process.run(
      'python',
      ['code/backend/stegocrypt_cli.py', 'hash', '--message', password],
    );
    if (result.exitCode == 0) {
      final jsonResponse = jsonDecode(result.stdout);
      return jsonResponse['hash'];
    } else {
      throw Exception('Failed to hash password');
    }
  }

  Future<void> _changePassword() async {
    final prefs = await SharedPreferences.getInstance();
    final savedPassword = prefs.getString('password');
    final oldPasswordHash = await _hashPassword(_oldPasswordController.text);
    if (savedPassword != oldPasswordHash) {
      setState(() {
        _errorText = 'Incorrect old password';
      });
      return;
    }
    if (_newPasswordController.text != _confirmPasswordController.text) {
      setState(() {
        _errorText = 'Passwords do not match';
      });
      return;
    }
    if (_newPasswordController.text.isEmpty) {
      setState(() {
        _errorText = 'Password cannot be empty';
      });
      return;
    }
    final newPasswordHash = await _hashPassword(_newPasswordController.text);
    await prefs.setString('password', newPasswordHash);
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(''),
      ),
      body: Center(
        child: Container(
          width: 400,
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text("Change Password",style: TextStyle(fontSize: 25.0,fontWeight: FontWeight.w500),),
                const SizedBox(height: 20),
                TextField(
                  controller: _oldPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Old Password',
                  ),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _newPasswordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'New Password',
                  ),
                ),
                const SizedBox(height: 20),
                TextField(
                  controller: _confirmPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'Confirm New Password',
                    errorText: _errorText,
                  ),
                ),
                const SizedBox(height: 20),
                ElevatedButton(
                  onPressed: _changePassword,
                  child: const Text('Change Password'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
