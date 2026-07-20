import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_config.dart';
import '../../data/datasources/api_client.dart';
import '../providers/server_config_provider.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  late TextEditingController _ipController;
  late TextEditingController _portController;
  ConnectionStatus _status = ConnectionStatus.idle;
  bool _disposed = false;

  @override
  void initState() {
    super.initState();
    _ipController = TextEditingController();
    _portController = TextEditingController();
    final configAsync = ref.read(serverConfigProvider);
    configAsync.whenData((config) {
      if (!_disposed) {
        _ipController.text = config.ip;
        _portController.text = config.port.toString();
      }
    });
  }

  Future<void> _testAndSave() async {
    final ip = _ipController.text.trim();
    final port = int.tryParse(_portController.text.trim()) ?? 0;
    if (ip.isEmpty || port == 0) return;

    setState(() => _status = ConnectionStatus.connecting);

    final config = ServerConfig(ip: ip, port: port);
    final apiClient = ApiClient(config);

    try {
      final health = await apiClient.health();
      final isOk = health['status'] == 'ok';
      if (!_disposed) {
        setState(() =>
            _status = isOk ? ConnectionStatus.connected : ConnectionStatus.failed);
      }

      if (isOk) {
        await ref
            .read(serverConfigProvider.notifier)
            .updateAndSave(config);
        if (!_disposed && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('اتصال موفق بود و تنظیمات ذخیره شد'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    } catch (e) {
      if (!_disposed) {
        setState(() => _status = ConnectionStatus.failed);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('تنظیمات سرور'),
        centerTitle: true,
      ),
      body: Directionality(
        textDirection: TextDirection.rtl,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _SectionHeader(
                icon: Icons.dns,
                title: 'پیکربندی اتصال سرور',
                subtitle: 'آدرس IP و پورت بک‌اند Frigate Intelligence را وارد کنید',
              ),
              const SizedBox(height: 28),
              Text('آدرس IP سرور',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              TextField(
                controller: _ipController,
                decoration: const InputDecoration(
                  hintText: '192.168.85.203',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.dns),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 20),
              Text('پورت', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              TextField(
                controller: _portController,
                decoration: const InputDecoration(
                  hintText: '8088',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.router),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton.icon(
                  onPressed:
                      _status == ConnectionStatus.connecting ? null : _testAndSave,
                  icon: _status == ConnectionStatus.connecting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.save),
                  label: const Text('ذخیره و اتصال'),
                ),
              ),
              const SizedBox(height: 20),
              _StatusIndicator(status: _status),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _disposed = true;
    _ipController.dispose();
    _portController.dispose();
    super.dispose();
  }
}

enum ConnectionStatus { idle, connecting, connected, failed }

class _StatusIndicator extends StatelessWidget {
  final ConnectionStatus status;
  const _StatusIndicator({required this.status});

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: Row(
        key: ValueKey(status),
        children: [
          Icon(
            switch (status) {
              ConnectionStatus.idle => Icons.circle_outlined,
              ConnectionStatus.connecting => Icons.sync,
              ConnectionStatus.connected => Icons.check_circle,
              ConnectionStatus.failed => Icons.error,
            },
            color: switch (status) {
              ConnectionStatus.idle => Colors.grey,
              ConnectionStatus.connecting => Colors.orange,
              ConnectionStatus.connected => Colors.green,
              ConnectionStatus.failed => Colors.red,
            },
            size: 20,
          ),
          const SizedBox(width: 8),
          Text(
            switch (status) {
              ConnectionStatus.idle => 'آماده',
              ConnectionStatus.connecting => 'در حال اتصال...',
              ConnectionStatus.connected => 'متصل ✓',
              ConnectionStatus.failed => 'اتصال ناموفق ✗',
            },
            style: TextStyle(
              color: switch (status) {
                ConnectionStatus.idle => Colors.grey,
                ConnectionStatus.connecting => Colors.orange,
                ConnectionStatus.connected => Colors.green,
                ConnectionStatus.failed => Colors.red,
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const _SectionHeader({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 28, color: Theme.of(context).colorScheme.primary),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
