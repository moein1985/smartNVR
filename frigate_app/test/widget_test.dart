// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:frigate_intelligence/main.dart';

void main() {
  testWidgets('Chat page renders with greeting and input bar', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: FrigateIntelligenceApp()),
    );
    await tester.pumpAndSettle();

    expect(find.text('Frigate Intelligence'), findsOneWidget);
    expect(find.byIcon(Icons.settings_outlined), findsOneWidget);
    expect(find.byIcon(Icons.mic_none), findsOneWidget);
    expect(find.byIcon(Icons.send_rounded), findsOneWidget);
  });
}
