import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/config/app_config.dart';
import '../../core/config/server_config_service.dart';
import '../../data/datasources/api_client.dart';
import '../../data/datasources/mock_api_client.dart';

final serverConfigServiceProvider = Provider<ServerConfigService>((ref) {
  return ServerConfigService();
});

final serverConfigProvider =
    AsyncNotifierProvider<ServerConfigNotifier, ServerConfig>(
  ServerConfigNotifier.new,
);

class ServerConfigNotifier extends AsyncNotifier<ServerConfig> {
  @override
  Future<ServerConfig> build() async {
    final service = ref.read(serverConfigServiceProvider);
    return service.load();
  }

  Future<void> updateAndSave(ServerConfig newConfig) async {
    final service = ref.read(serverConfigServiceProvider);
    await service.save(newConfig);
    state = AsyncValue.data(newConfig);
  }
}

final apiClientProvider = Provider<BaseApiClient>((ref) {
  final configAsync = ref.watch(serverConfigProvider);
  return configAsync.maybeWhen(
    data: (config) {
      if (config.isMockMode) {
        return MockApiClient();
      }
      return ApiClient(config);
    },
    orElse: () => ApiClient(const ServerConfig(ip: '0.0.0.0', port: 0)),
  );
});
