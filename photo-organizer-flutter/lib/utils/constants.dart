class ApiConfig {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration uploadTimeout = Duration(seconds: 120);

  static const int maxRetries = 3;
  static const int pollIntervalMs = 3000;
}
