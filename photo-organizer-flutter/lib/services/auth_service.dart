import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthService extends ChangeNotifier {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  bool _isAuthenticated = false;
  String? _userId;

  bool get isAuthenticated => _isAuthenticated;
  String? get userId => _userId;

  Future<void> checkAuth() async {
    final token = await _storage.read(key: 'access_token');
    _isAuthenticated = token != null;
    _userId = await _storage.read(key: 'user_id');
    notifyListeners();
  }

  Future<void> setAuth(String token, String userId) async {
    await _storage.write(key: 'access_token', value: token);
    await _storage.write(key: 'user_id', value: userId);
    _isAuthenticated = true;
    _userId = userId;
    notifyListeners();
  }

  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'user_id');
    _isAuthenticated = false;
    _userId = null;
    notifyListeners();
  }
}
