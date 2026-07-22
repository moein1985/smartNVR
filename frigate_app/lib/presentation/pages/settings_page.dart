import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import '../../core/config/app_config.dart';
import '../../data/datasources/api_client.dart';
import '../providers/server_config_provider.dart';
import '../providers/settings_provider.dart';
import '../providers/system_maintenance_provider.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  late TextEditingController _ipController;
  late TextEditingController _portController;
  late TextEditingController _botTokenController;
  late TextEditingController _chatIdController;
  late TextEditingController _reportIntervalController;
  ConnectionStatus _status = ConnectionStatus.idle;
  bool _disposed = false;
  bool _isMockMode = false;
  bool _telegramEnabled = false;
  String _reportTimezone = 'Asia/Tehran';

  static const _timezones = [
    'Asia/Tehran',
    'UTC',
    'Europe/London',
    'America/New_York',
    'Asia/Dubai',
  ];

  @override
  void initState() {
    super.initState();
    _ipController = TextEditingController();
    _portController = TextEditingController();
    _botTokenController = TextEditingController();
    _chatIdController = TextEditingController();
    _reportIntervalController = TextEditingController(text: '24');
    final configAsync = ref.read(serverConfigProvider);
    configAsync.whenData((config) {
      if (!_disposed) {
        _ipController.text = config.ip;
        _portController.text = config.port.toString();
        _isMockMode = config.isMockMode;
      }
    });
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    try {
      final client = ref.read(apiClientProvider);
      final settings = await client.getSettings();
      if (!_disposed) {
        setState(() {
          _telegramEnabled = settings['telegram_enabled'] as bool? ?? false;
          _botTokenController.text =
              settings['telegram_bot_token'] as String? ?? '';
          _chatIdController.text =
              settings['telegram_chat_id'] as String? ?? '';
          _reportIntervalController.text =
              (settings['report_interval_hours'] ?? 24).toString();
          _reportTimezone =
              settings['report_timezone'] as String? ?? 'Asia/Tehran';
        });
      }
    } catch (_) {
      // Settings unavailable (e.g. mock mode or server down)
    }
  }

  Future<void> _saveTelegramSettings() async {
    final newSettings = <String, dynamic>{
      'telegram_enabled': _telegramEnabled,
      'telegram_bot_token': _botTokenController.text.trim(),
      'telegram_chat_id': _chatIdController.text.trim(),
      'report_interval_hours':
          int.tryParse(_reportIntervalController.text.trim()) ?? 24,
      'report_timezone': _reportTimezone,
      'report_target': 'telegram',
    };
    try {
      await ref.read(settingsProvider.notifier).updateSettings(newSettings);
      if (!_disposed && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('تنظیمات تلگرام ذخیره شد'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (_) {
      if (!_disposed && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('خطا در ذخیره تنظیمات'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _testAndSave() async {
    final ip = _ipController.text.trim();
    final port = int.tryParse(_portController.text.trim()) ?? 0;
    if (ip.isEmpty || port == 0) return;

    final config = ServerConfig(ip: ip, port: port, isMockMode: _isMockMode);

    if (_isMockMode) {
      await ref.read(serverConfigProvider.notifier).updateAndSave(config);
      if (!_disposed && mounted) {
        setState(() => _status = ConnectionStatus.connected);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('حالت آفلاین فعال شد - داده‌های تستی'),
            backgroundColor: Colors.blue,
          ),
        );
      }
      return;
    }

    setState(() => _status = ConnectionStatus.connecting);

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
              SwitchListTile(
                title: const Text('حالت آفلاین'),
                subtitle: const Text('استفاده از داده‌های تستی بدون اتصال به سرور'),
                secondary: const Icon(Icons.cloud_off),
                value: _isMockMode,
                onChanged: (value) {
                  setState(() {
                    _isMockMode = value;
                    _status = ConnectionStatus.idle;
                  });
                },
              ),
              const Divider(height: 32),
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
              const SizedBox(height: 40),
              const _SectionHeader(
                icon: Icons.send,
                title: 'تلگرام و گزارش‌گیری',
                subtitle: 'تنظیمات ربات تلگرام و زمان‌بندی گزارش‌های روزانه',
              ),
              const SizedBox(height: 28),
              SwitchListTile(
                title: const Text('فعال‌سازی گزارش‌های زمان‌بندی شده'),
                subtitle: const Text('ارسال خودکار گزارش روزانه به تلگرام'),
                secondary: const Icon(Icons.notifications_active),
                value: _telegramEnabled,
                onChanged: (value) {
                  setState(() => _telegramEnabled = value);
                },
              ),
              const SizedBox(height: 20),
              Text('Telegram Bot Token',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              TextField(
                controller: _botTokenController,
                decoration: const InputDecoration(
                  hintText: '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.key),
                ),
                obscureText: true,
                enabled: _telegramEnabled,
              ),
              const SizedBox(height: 20),
              Text('Telegram Chat ID',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              TextField(
                controller: _chatIdController,
                decoration: const InputDecoration(
                  hintText: '-1001234567890',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.chat),
                ),
                keyboardType: TextInputType.number,
                enabled: _telegramEnabled,
              ),
              const SizedBox(height: 20),
              Text('بازه گزارش‌گیری (ساعت)',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              TextFormField(
                controller: _reportIntervalController,
                decoration: const InputDecoration(
                  hintText: '24',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.schedule),
                ),
                keyboardType: TextInputType.number,
                enabled: _telegramEnabled,
                validator: (value) {
                  final hours = int.tryParse(value ?? '');
                  if (hours == null || hours < 1) {
                    return 'عدد بزرگ‌تر از ۰ وارد کنید';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 20),
              Text('منطقه زمانی',
                  style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _reportTimezone,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.public),
                ),
                items: _timezones
                    .map((tz) => DropdownMenuItem(
                          value: tz,
                          child: Text(tz),
                        ))
                    .toList(),
                onChanged: _telegramEnabled
                    ? (value) {
                        if (value != null) {
                          setState(() => _reportTimezone = value);
                        }
                      }
                    : null,
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: FilledButton.icon(
                  onPressed: _telegramEnabled ? _saveTelegramSettings : null,
                  icon: const Icon(Icons.save),
                  label: const Text('ذخیره تنظیمات تلگرام'),
                ),
              ),
              const SizedBox(height: 40),
              const _SectionHeader(
                icon: Icons.build,
                title: 'نگهداری سیستم',
                subtitle: 'مشاهده لاگ‌های سیستم و به‌روزرسانی OTA',
              ),
              const SizedBox(height: 28),
              _SystemMaintenanceSection(),
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
    _botTokenController.dispose();
    _chatIdController.dispose();
    _reportIntervalController.dispose();
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

class _SystemMaintenanceSection extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final maintenanceState = ref.watch(systemMaintenanceProvider);

    ref.listen<SystemMaintenanceState>(systemMaintenanceProvider, (previous, next) {
      if (next.updateState == UpdateState.success && next.message != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message!),
            backgroundColor: Colors.green,
          ),
        );
        ref.read(systemMaintenanceProvider.notifier).reset();
      } else if (next.updateState == UpdateState.rolledBack &&
          next.message != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message!),
            backgroundColor: Colors.orange,
          ),
        );
        ref.read(systemMaintenanceProvider.notifier).reset();
      } else if (next.updateState == UpdateState.failed &&
          next.message != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.message!),
            backgroundColor: Colors.red,
          ),
        );
        ref.read(systemMaintenanceProvider.notifier).reset();
      }
    });

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.terminal, size: 20),
            const SizedBox(width: 8),
            Text('لاگ‌های سیستم',
                style: Theme.of(context).textTheme.labelLarge),
            const Spacer(),
            TextButton.icon(
              onPressed: maintenanceState.isLoadingLogs
                  ? null
                  : () =>
                      ref.read(systemMaintenanceProvider.notifier).fetchLogs(),
              icon: maintenanceState.isLoadingLogs
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh, size: 18),
              label: const Text('بازنشانی'),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          height: 200,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF1E1E1E),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey.shade700),
          ),
          child: SingleChildScrollView(
            scrollDirection: Axis.vertical,
            child: SelectableText(
              maintenanceState.logs ??
                  'برای مشاهده لاگ‌ها روی «بازنشانی» بزنید',
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 11,
                color: Color(0xFFD4D4D4),
                height: 1.4,
              ),
            ),
          ),
        ),
        const SizedBox(height: 28),
        Text('به‌روزرسانی OTA',
            style: Theme.of(context).textTheme.labelLarge),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          height: 48,
          child: FilledButton.icon(
            onPressed: maintenanceState.updateState == UpdateState.uploading
                ? null
                : () => _pickAndUpdateFile(context, ref),
            icon: maintenanceState.updateState == UpdateState.uploading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : const Icon(Icons.system_update),
            label: Text(
              maintenanceState.updateState == UpdateState.uploading
                  ? 'در حال به‌روزرسانی...'
                  : 'انتخاب فایل به‌روزرسانی (.tar)',
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _pickAndUpdateFile(
      BuildContext context, WidgetRef ref) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['tar'],
    );
    if (result != null && result.files.isNotEmpty) {
      final filePath = result.files.first.path;
      if (filePath != null) {
        ref.read(systemMaintenanceProvider.notifier).uploadUpdate(filePath);
      }
    }
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
