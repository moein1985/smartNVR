import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'chat_page.dart';
import 'classic_nvr_page.dart';
import 'settings_page.dart';
import '../providers/time_sync_provider.dart';

class MainScaffold extends ConsumerStatefulWidget {
  const MainScaffold({super.key});

  @override
  ConsumerState<MainScaffold> createState() => _MainScaffoldState();
}

class _MainScaffoldState extends ConsumerState<MainScaffold> {
  int _currentIndex = 0;

  final pages = const [
    ChatPage(),
    ClassicNVRPage(),
    SettingsPage(),
  ];

  static const _destinations = [
    (icon: Icons.smart_toy_outlined, selectedIcon: Icons.smart_toy, label: 'AI'),
    (icon: Icons.videocam_outlined, selectedIcon: Icons.videocam, label: 'NVR'),
    (icon: Icons.settings_outlined, selectedIcon: Icons.settings, label: 'Settings'),
  ];

  Widget _buildSkewBanner() {
    final timeSync = ref.watch(timeSyncProvider);
    if (!timeSync.hasSignificantSkew) return const SizedBox.shrink();

    final skewMin = timeSync.skew!.inMinutes.abs();
    final direction = timeSync.skew!.isNegative ? 'behind' : 'ahead';

    return MaterialBanner(
      content: Text(
        '⚠️ Clock skew detected: client is $skewMin minutes $direction of server. '
        'Timestamps may be inaccurate.',
        style: const TextStyle(fontSize: 13),
      ),
      backgroundColor: Colors.orange.shade900,
      actions: [
        TextButton(
          onPressed: () => ref.read(timeSyncProvider.notifier).checkSync(),
          child: const Text('Retry'),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final skewBanner = _buildSkewBanner();

    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth > 600;

        if (isWide) {
          return Scaffold(
            body: Column(
              children: [
                skewBanner,
                Expanded(
                  child: Row(
                    children: [
                      NavigationRail(
                        selectedIndex: _currentIndex,
                        onDestinationSelected: (i) =>
                            setState(() => _currentIndex = i),
                        extended: constraints.maxWidth > 900,
                        destinations: [
                          for (final d in _destinations)
                            NavigationRailDestination(
                              icon: Icon(d.icon),
                              selectedIcon: Icon(d.selectedIcon),
                              label: Text(d.label),
                            ),
                        ],
                      ),
                      const VerticalDivider(thickness: 1, width: 1),
                      Expanded(
                        child: IndexedStack(index: _currentIndex, children: pages),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }

        return Scaffold(
          body: Column(
            children: [
              skewBanner,
              Expanded(
                child: IndexedStack(index: _currentIndex, children: pages),
              ),
            ],
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _currentIndex,
            onDestinationSelected: (i) =>
                setState(() => _currentIndex = i),
            destinations: [
              for (final d in _destinations)
                NavigationDestination(
                  icon: Icon(d.icon),
                  selectedIcon: Icon(d.selectedIcon),
                  label: d.label,
                ),
            ],
          ),
        );
      },
    );
  }
}
