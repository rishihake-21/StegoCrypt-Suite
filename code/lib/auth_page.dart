import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:stegocrypt_suite/change_password_page.dart';
import 'package:stegocrypt_suite/main_layout.dart';
import 'cyber_theme.dart';

class AuthPage extends StatefulWidget {
  const AuthPage({super.key});

  @override
  State<AuthPage> createState() => _AuthPageState();
}

class _AuthPageState extends State<AuthPage> {
  final TextEditingController _passwordController = TextEditingController();
  bool _isPasswordSet = false;
  String? _errorText;

  @override
  void initState() {
    super.initState();
    _checkPassword();
  }

  Future<void> _checkPassword() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _isPasswordSet = prefs.containsKey('password');
    });
  }

  String _hashPassword(String password) {
    final bytes = utf8.encode(password);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  Future<void> _setPassword() async {
    if (_passwordController.text.isEmpty) {
      setState(() {
        _errorText = 'Password cannot be empty';
      });
      return;
    }
    final hashedPassword = _hashPassword(_passwordController.text);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('password', hashedPassword);
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (context) => const MainLayout()),
    );
  }

  Future<void> _verifyPassword() async {
    final prefs = await SharedPreferences.getInstance();
    final savedPassword = prefs.getString('password');
    final hashedPassword = _hashPassword(_passwordController.text);
    if (savedPassword == hashedPassword) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const MainLayout()),
      );
    } else {
      setState(() {
        _errorText = 'Incorrect password';
      });
    }
  }

  Widget _buildLogoSection() {
    return Container(
      padding: const EdgeInsets.all(32),
      child: Column(
        children: [
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
            ),
            child: Center(
              child: ClipOval(
                child: Image.asset("assets/logo/sc2.jpg",
                fit: BoxFit.cover,
                width: 100,
                height: 100,),
              )
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'StegoCrypt',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
          Text(
            'Suite',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w400,
              color: CyberTheme.aquaBlue,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 0,
        elevation:0
      ),
      body: Center(
        child: Container(
          width: 400,
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child:
            Column(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                _buildLogoSection(),
                const SizedBox(height: 80),
                Row(
                  mainAxisAlignment: MainAxisAlignment.start,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Text(_isPasswordSet ? 'Enter Password:' : 'Set Password:',style: TextStyle(
                      fontWeight: FontWeight.w500,
                      fontSize: 25.0
                    )
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
                const SizedBox(height: 20),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    TextField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: InputDecoration(
                        labelText: 'Password',
                        errorText: _errorText,
                      ),
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: _isPasswordSet ? _verifyPassword : _setPassword,
                      child: Text(_isPasswordSet ? 'Unlock' : 'Set Password'),
                    ),
                    const SizedBox(height: 20),
                    if (_isPasswordSet)
                      TextButton(
                        onPressed: _navigateToChangePasswordPage,
                        child: const Text('Change Password'),
                      ),
                  ],
                )
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _navigateToChangePasswordPage() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const ChangePasswordPage()),
    );
  }
}
