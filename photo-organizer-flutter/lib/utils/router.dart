import 'package:go_router/go_router.dart';
import 'package:photo_organizer/screens/home_screen.dart';
import 'package:photo_organizer/screens/album_screen.dart';
import 'package:photo_organizer/screens/organize_screen.dart';
import 'package:photo_organizer/screens/results_screen.dart';
import 'package:photo_organizer/screens/photo_detail_screen.dart';
import 'package:photo_organizer/screens/settings_screen.dart';
import 'package:photo_organizer/screens/login_screen.dart';
import 'package:photo_organizer/screens/shell_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),
    ShellRoute(
      builder: (context, state, child) => ShellScreen(child: child),
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const HomeScreen(),
        ),
        GoRoute(
          path: '/album',
          builder: (context, state) => const AlbumScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
      ],
    ),
    GoRoute(
      path: '/organize/:taskId',
      builder: (context, state) => OrganizeScreen(
        taskId: state.pathParameters['taskId']!,
      ),
    ),
    GoRoute(
      path: '/results/:taskId',
      builder: (context, state) => ResultsScreen(
        taskId: state.pathParameters['taskId']!,
      ),
    ),
    GoRoute(
      path: '/photo/:photoId',
      builder: (context, state) => PhotoDetailScreen(
        photoId: state.pathParameters['photoId']!,
      ),
    ),
  ],
);
