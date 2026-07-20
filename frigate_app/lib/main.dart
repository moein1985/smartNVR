import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'presentation/pages/chat_page.dart';

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
      theme: AppTheme.dark(),
      home: const ChatPage(),
    );
  }
}
