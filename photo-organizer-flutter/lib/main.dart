import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:photo_organizer/services/auth_service.dart';
import 'package:photo_organizer/services/api_service.dart';
import 'package:photo_organizer/utils/router.dart';
import 'package:photo_organizer/utils/theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PhotoOrganizerApp());
}

class PhotoOrganizerApp extends StatelessWidget {
  const PhotoOrganizerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        Provider(create: (_) => ApiService()),
      ],
      child: MaterialApp.router(
        title: '智能图片整理',
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routerConfig: appRouter,
        debugShowCheckedModeBanner: false,
      ),
    );
  }
}
