import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'server_config_provider.dart';

final settingsProvider =
    AsyncNotifierProvider<SettingsNotifier, Map<String, dynamic>>(
  SettingsNotifier.new,
);

class SettingsNotifier extends AsyncNotifier<Map<String, dynamic>> {
  @override
  Future<Map<String, dynamic>> build() async {
    final client = ref.read(apiClientProvider);
    return client.getSettings();
  }

  Future<void> updateSettings(Map<String, dynamic> newSettings) async {
    final client = ref.read(apiClientProvider);
    await client.updateSettings(newSettings);
    state = AsyncValue.data(newSettings);
  }
}
