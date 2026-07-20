import 'package:shared_preferences/shared_preferences.dart';
import 'app_config.dart';

class ServerConfigService {
  static const _keyIp = 'server_ip';
  static const _keyPort = 'server_port';
  static const _keyMockMode = 'server_mock_mode';

  static const ServerConfig _default =
      ServerConfig(ip: '192.168.85.203', port: 8088);

  Future<ServerConfig> load() async {
    final prefs = await SharedPreferences.getInstance();
    final ip = prefs.getString(_keyIp) ?? _default.ip;
    final port = prefs.getInt(_keyPort) ?? _default.port;
    final isMockMode = prefs.getBool(_keyMockMode) ?? false;
    return ServerConfig(ip: ip, port: port, isMockMode: isMockMode);
  }

  Future<void> save(ServerConfig config) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyIp, config.ip);
    await prefs.setInt(_keyPort, config.port);
    await prefs.setBool(_keyMockMode, config.isMockMode);
  }
}
