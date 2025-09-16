// main_dart.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:window_manager/window_manager.dart';
import 'cyber_theme.dart';
import 'app_routes.dart';
import 'app_provider.dart';
import 'main_layout.dart';
import 'package:flutter/foundation.dart' show kIsWeb, defaultTargetPlatform, TargetPlatform;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Configure window for desktop only (skip web and mobile)
  final bool isDesktop = !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.windows ||
          defaultTargetPlatform == TargetPlatform.linux ||
          defaultTargetPlatform == TargetPlatform.macOS);

  if (isDesktop) {
    await windowManager.ensureInitialized();

    const WindowOptions windowOptions = WindowOptions(
      size: Size(1920, 1080), // Full HD size
      center: true,
      backgroundColor: const Color(0xFF0A0A0A), // Dark background to match cyber theme
      skipTaskbar: false,
      titleBarStyle: TitleBarStyle.normal, // Show native title bar with OS controls
      minimumSize: Size(1200, 800),
      maximumSize: Size(1920, 1080),
      windowButtonVisibility: true, // Show native window buttons
      title: 'StegoCrypt Suite', // App title in title bar
    );

    windowManager.waitUntilReadyToShow(windowOptions, () async {
      await windowManager.show();
      await windowManager.focus();
      // Open maximized by default
      await windowManager.maximize();
    });
  }

  runApp(const StegoCryptApp());
}

class StegoCryptApp extends StatelessWidget {
  const StegoCryptApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [ChangeNotifierProvider(create: (_) => AppProvider())],
      child: Consumer<AppProvider>(

        builder: (context, appProvider, _) {
          return MaterialApp(
            title: 'StegoCrypt Suit',
            theme: CyberTheme.lightTheme,
            darkTheme: CyberTheme.darkTheme,
            themeMode: appProvider.themeMode,
            debugShowCheckedModeBanner: false,
            home: const MainLayout(),
            onGenerateRoute: AppRoutes.generateRoute,
          );
        },
      ),
    );
  }
}


