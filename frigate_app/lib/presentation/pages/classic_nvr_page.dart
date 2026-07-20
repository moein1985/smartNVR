import 'package:flutter/material.dart';
import 'live_view_tab.dart';
import 'playback_tab.dart';

class ClassicNVRPage extends StatelessWidget {
  const ClassicNVRPage({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('NVR'),
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.live_tv), text: 'زنده'),
              Tab(icon: Icon(Icons.history), text: 'پخش'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            LiveViewTab(),
            PlaybackTab(),
          ],
        ),
      ),
    );
  }
}
