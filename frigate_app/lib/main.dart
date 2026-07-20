import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'presentation/pages/settings_page.dart';

void main() {
  runApp(const ProviderScope(child: FrigateIntelligenceApp()));
}

class FrigateIntelligenceApp extends StatelessWidget {
  const FrigateIntelligenceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Frigate Intelligence',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.cyan,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const SettingsPage(),
    );
  }
}
