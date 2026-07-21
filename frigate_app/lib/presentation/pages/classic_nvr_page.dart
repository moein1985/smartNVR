import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'live_view_tab.dart';
import 'playback_tab.dart';
import '../providers/navigation_provider.dart';

class ClassicNVRPage extends ConsumerStatefulWidget {
  const ClassicNVRPage({super.key});

  @override
  ConsumerState<ClassicNVRPage> createState() => _ClassicNVRPageState();
}

class _ClassicNVRPageState extends ConsumerState<ClassicNVRPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.listenManual(navigationProvider, (prev, next) {
        if (prev?.nvrSubTabIndex != next.nvrSubTabIndex) {
          _tabController.animateTo(next.nvrSubTabIndex);
        }
      });
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('NVR'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.live_tv), text: 'زنده'),
            Tab(icon: Icon(Icons.history), text: 'پخش'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          LiveViewTab(),
          PlaybackTab(),
        ],
      ),
    );
  }
}
